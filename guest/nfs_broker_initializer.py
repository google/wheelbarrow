#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Author: octeau@cse.psu.edu (Damien Octeau)
# Author: theinsecureroot@gmail.com (Cyrus Vesuna)
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""An NFS broker initializer."""


import glob
import logging
import os
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from collections import namedtuple
from google.protobuf.message import EncodeError
from common import wheelbarrow_pb2
from common.utils import ParseFileToProtobuf
from guest import broker_initializer


class NfsBrokerInitializer(broker_initializer.BrokerInitializer):
  """A broker initializer for the case of an NFS configuration."""

  def __init__(self, config_path):
    """Constructor.

    Args:
        config_path: Path to an NFS configuration file.
    """

    self._config_path = config_path
    self._pending_descriptor_path = None

  def InitializeBroker(self):
    """Initialize the broker.

    Returns:
      The analysis context.
    """

    config = NfsBrokerInitializer._LoadConfigFromFile(self._config_path)
    # Start logging to NFS as soon as possible to be able to debug issues in the
    # _MakePendingPackageDescriptor() call.
    logfile = os.path.join(config.log_dir, 'broker.log')

    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    descriptor = self._MakePendingPackageDescriptor(config)
    name = '%s-%s-%s' % (descriptor.name, descriptor.version,
                         descriptor.architecture)
    # Set more useful logging file names.

    logfile = os.path.join(config.log_dir, name)
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    context = namedtuple(
        'nfs', 'package_descriptor, config, pending_descriptor_path')
    return context(descriptor, config, self._pending_descriptor_path)

  @staticmethod
  def _LoadConfigFromFile(path):
    """Load a configuration protobuf from a file.

    Args:
      path: The path to a wheelbarrow_pb2.NfsAnalysisConfig in binary format.

    Returns:
      A wheelbarrow_pb2.NfsAnalysisConfig.

    Raises:
      InitializationError if the configuration cannot be loaded.
    """

    config = wheelbarrow_pb2.NfsAnalysisConfig()

    if not ParseFileToProtobuf(path, config, -1, False):
      error = 'Could not parse configuration file %s.' % path
      logging.error(error)
      raise broker_initializer.InitializationError(error)
    return config

  def _MakePendingPackageDescriptor(self, config):
    """Find a package and generate and write a pending package descriptor.

    Before starting an analysis, a "pending" package descriptor is written to
    the NFS share so that other VMs do not analyze the same package.

    Args:
      config: A wheelbarrow_pb2.NfsAnalysisConfig for this analysis.

    Returns:
      The wheelbarrow_pb2.Package for this analysis.

    Raises:
      NoPackageError if no package could be found and locked.
    """

    path = os.path.join(config.input_dir, '*')
    package_descriptors = glob.glob(path)
    descriptor_count = len(package_descriptors)
    logging.info('Found %d packages.', descriptor_count)
    if descriptor_count == 0:
      raise broker_initializer.NoPackageError('No package found for analysis in'
                                              '%s.' % path)
    for package_descriptor_path in package_descriptors:
      # Lock the package descriptor before even trying to read it.
      # If we read before locking, another broker might have already locked and
      # deleted the descriptor, resulting in a read error.
      descriptor_file = self._LockPendingDescriptor(config,
                                                    package_descriptor_path)
      if not descriptor_file:
        # The pending descriptor file could not be created.
        continue
      package_descriptor = NfsBrokerInitializer._LoadPackageDescriptorFromFile(
          package_descriptor_path)
      NfsBrokerInitializer._WriteToPendingDescriptorFile(package_descriptor,
                                                         descriptor_file)
      # Remove the package from the list of packages to be processed.
      os.remove(package_descriptor_path)
      if os.path.exists(package_descriptor_path):
        logging.error('Could not remove file %s.', package_descriptor_path)
      return package_descriptor
    # Not a single package could be locked.
    raise broker_initializer.NoPackageError('No package found for analysis in '
                                            'NFS input directory.')

  def _LockPendingDescriptor(self, config, descriptor_path):
    """Lock a package by atomically writing a pending descriptor for it.

    This function guarantees that a package will only be analyzed by the
    current VM. It atomically writes a pending descriptor file if the file does
    not already exist. It returns a file descriptor, which should be closed by
    the caller.

    Args:
      config: The wheelbarrow_pb2.NfsAnalysisConfig for this package.
      descriptor_path: The path to the input wheelbarrow_pb2.Package.

    Returns:
      The file descriptor of the written pending descriptor if all goes well,
      None otherwise.
    """

    self._pending_descriptor_path = os.path.join(
        config.output_dir, '%s.pending' % os.path.basename(descriptor_path))
    if os.path.exists(self._pending_descriptor_path):
      return None
    try:
      descriptor_file = os.open(self._pending_descriptor_path,
                                os.O_CREAT | os.O_EXCL | os.O_WRONLY)
      return descriptor_file
    except OSError as e:
      logging.warning('Could not create pending descriptor file %s: %s',
                      self._pending_descriptor_path, e)
      return None

  @staticmethod
  def _WriteToPendingDescriptorFile(descriptor, pending_descriptor_file):
    """Write a pending package descriptor (wheelbarrow_pb2.Package) to file.

    This method closes the file descriptor after writing to the file.

    Args:
      descriptor: A wheelbarrow_pb2.Package.
      pending_descriptor_file: A file descriptor.

    Raises:
      InitializationError if a file operation goes wrong.
    """

    descriptor.status = wheelbarrow_pb2.Package.PROCESSING
    descriptor.analysis_attempts += 1
    try:
      os.write(pending_descriptor_file, descriptor.SerializePartialToString())
      os.close(pending_descriptor_file)
    except (OSError, EncodeError) as e:
      logging.error('Could not write to pending package descriptor: %s', e)
      raise broker_initializer.InitializationError('Could not write to pending'
                                                   'package descriptor.')

  @staticmethod
  def _LoadPackageDescriptorFromFile(path):
    """Load a package descriptor from a file.

    Args:
      path: Path to a file containing a wheelbarrow_pb2.Package, either in text
            or binary format. A text format protobuf is assumed to have
            extension .txt, whereas a binary format protobuf is assumed to have
            extension .dat.

    Returns:
      A wheelbarrow_pb2.Package.

    Raises:
      broker_initializer.InitializationError if something goes wrong when
      opening or parsing the file.
    """

    package_descriptor = wheelbarrow_pb2.Package()
    if ParseFileToProtobuf(path, package_descriptor):
      return package_descriptor
    else:
      error = 'Could not load and parse package descriptor file %s.' % path
      logging.error(error)
      raise broker_initializer.InitializationError(error)
