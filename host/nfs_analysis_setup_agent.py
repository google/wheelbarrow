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
"""NFS analysis setup."""

import apt
import apt_pkg
import logging
import os
import os.path
import re
import shutil
import stat
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)
from common import utils
from common import wheelbarrow_pb2
from host import vm_launcher


class NfsAnalysisSetupAgent(object):
  """Setup agent for an analysis using an NFS share.

  This class sets up the directories and files necessary for an analysis
  using an NFS share to communicate with the guest.
  """

  CONFIG_FILE_NAME = 'analysis.config'
  INPUT_DIR = 'in'
  ERROR = -1
  OUTPUT_DIR = 'out'
  _LOG_DIR = 'log'
  _INSTALL_BASE_DIR = WHEELBARROW_HOME
  _LAUNCHERS_BASE_DIR = 'host/launchers'
  _DEST_LAUNCHER_FILE_NAME = 'nfs_launcher.sh'

  def __init__(self, host_nfs_share, guest_nfs_share, timeout,
               text_output=False, update=False, broker=False, image=None):
    self._host_nfs_share = host_nfs_share
    self._dest_launcher_path = os.path.join(
        self._host_nfs_share,
        NfsAnalysisSetupAgent._DEST_LAUNCHER_FILE_NAME)
    self._guest_nfs_share = guest_nfs_share
    self._timeout = timeout
    self._text_output = text_output
    self._update = update
    self._broker = broker
    self._image = image

  def SetUpAnalysis(self, batch_descriptor_path):
    """Set up the analysis.

    Args:
      batch_descriptor_path: The path to a
                             wheelbarrow_pb2.BatchPackageDescriptor in text
                             format.

    Returns:
      The number of packages to be analyzed, or ERROR if there was a problem.
    """

    if self._broker and not self._UpdateBroker():
      return NfsAnalysisSetupAgent.ERROR
    if not self._SetUpBrokerRunLauncher():
      return NfsAnalysisSetupAgent.ERROR
    batch_descriptor = NfsAnalysisSetupAgent._LoadBatchDescriptorFromFile(
        batch_descriptor_path)
    if not batch_descriptor:
      return NfsAnalysisSetupAgent.ERROR
    return self._SetUpAnalysisFromBatchDescriptor(batch_descriptor)

  def _UpdateBroker(self):
    """Setup Broker paths."""
    logging.info('Updating broker on VM image...')
    set_up_launcher_path = os.path.join(
        NfsAnalysisSetupAgent._INSTALL_BASE_DIR,
        NfsAnalysisSetupAgent._LAUNCHERS_BASE_DIR,
        'nfs_set_up_launcher.sh')
    cmd = vm_launcher.MakeVmCommand(self._image, 2048, False)
    mymsg = 'Running with args: %s' % cmd
    logging.info(mymsg)
    return (self._CopyBrokerLauncher(set_up_launcher_path)
            and vm_launcher.StartVm(cmd, 1200))

  def _SetUpBrokerRunLauncher(self):
    """Setup Broker paths."""
    run_launcher_path = os.path.join(
        NfsAnalysisSetupAgent._INSTALL_BASE_DIR,
        NfsAnalysisSetupAgent._LAUNCHERS_BASE_DIR,
        'nfs_run_launcher.sh')
    return self._CopyBrokerLauncher(run_launcher_path)

  def _CopyBrokerLauncher(self, src):
    """Copy over launcher if it doesn't exist."""
    try:
      logging.info(self._dest_launcher_path)
      os.remove(self._dest_launcher_path)
    except OSError:
      pass
    try:
      logging.info(self._dest_launcher_path)
      shutil.copyfile(src, self._dest_launcher_path)
      os.chmod(self._dest_launcher_path, stat.S_IRUSR | stat.S_IXUSR)
      return True
    except (IOError, shutil.Error) as err:
      logging.error('Error while copying NFS launcher: %s', err)
      return False

  def _SetUpAnalysisFromBatchDescriptor(self, batch_descriptor):
    """Put together a list of packages that match the specified regexs."""
    apt_pkg.init()
    architecture = batch_descriptor.architecture.encode('utf8')
    apt_pkg.config['Apt::Architecture'] = architecture
    cache = apt.Cache()
    if self._update:
      try:
        cache.update()
      except apt.cache.FetchFailedException as err:
        logging.warning('Failed to update apt cache: %s', err)
    cache.open(None)

    name_compiled_regex = re.compile(batch_descriptor.name_regex)

    if self._SetUpDirs() and self._SetUpConfigFile():
      return self._SetUpPackageDescriptors(cache, name_compiled_regex,
                                           batch_descriptor.architecture,
                                           batch_descriptor.max_count)
    else:
      return NfsAnalysisSetupAgent.ERROR

  @staticmethod
  def _LoadBatchDescriptorFromFile(batch_descriptor_path):
    """Load a batch package descriptor from a file.

    Args:
      batch_descriptor_path: The path to a file containing a batch package
                             protobuf in text format.

    Returns:
      A batch package descriptor is all goes well, None otherwise.
    """

    batch_package_descriptor = wheelbarrow_pb2.BatchPackageDescriptor()

    if utils.ParseFileToProtobuf(batch_descriptor_path,
                                 batch_package_descriptor, -1, True):
      return batch_package_descriptor
    else:
      return None

  def _SetUpDirs(self):
    """Check/create INPUT_DIR, OUTPUT_DIR, _LOG_DIR if they don't exist."""
    logging.info('Setting up directories...')
    host_input_dir = os.path.join(self._host_nfs_share,
                                  NfsAnalysisSetupAgent.INPUT_DIR)
    host_output_dir = os.path.join(self._host_nfs_share,
                                   NfsAnalysisSetupAgent.OUTPUT_DIR)
    host_log_dir = os.path.join(self._host_nfs_share,
                                NfsAnalysisSetupAgent._LOG_DIR)
    try:
      NfsAnalysisSetupAgent._CreateDirIfNotExists(host_input_dir)
      NfsAnalysisSetupAgent._CreateDirIfNotExists(host_output_dir)
      NfsAnalysisSetupAgent._CreateDirIfNotExists(host_log_dir)
      return True
    except OSError as err:
      logging.error('Could not set up directories: %s', err)
      return False

  @staticmethod
  def _CreateDirIfNotExists(path):
    """If specified directory doesn't exist, create it."""
    if not os.path.exists(path):
      os.makedirs(path)

  def _SetUpPackageDescriptors(self, cache, name_compiled_regex, architecture,
                               max_count):
    """Set up package descriptors.

    Args:
      cache: An apt cache.
      name_compiled_regex: A compiled regular expression representing the
                           package names that should be selected.
      architecture: The architecture of the packages that should be selected.
      max_count: The maximum number of packages to select.

    Returns:
      The number of packages to be analyzed, or ERROR if something went wrong.
    """

    logging.info('Setting up package descriptors...')
    count = 0
    for package in cache:
      if not self._SelectPackage(package, name_compiled_regex, cache):
        continue
      for version in package.versions:
        if not self._SelectVersion(version, architecture):
          continue
        if not self._WritePackageDescriptorToFile(package.name, version):
          return NfsAnalysisSetupAgent.ERROR
        count += 1
        if max_count and count >= max_count:
          return count
    return count

  def _SelectPackage(self, package, name_compiled_regex, cache):
    """Determine if a package should be selected.

    Args:
      package: A candidate package.
      name_compiled_regex: A compiled regular expression representing the names
                           of packages that should be selected.
      cache: An apt cache.

    Returns:
      True if the argument package should be selected.
    """

    return (name_compiled_regex.match(package.name)
            and not cache.is_virtual_package(package.name))

  def _SelectVersion(self, version, architecture):
    """Determine if a package version should be selected.

    Args:
      version: A package version.
      architecture: The desired architecture.

    Returns:
      True if the version should be selected.
    """

    return version.architecture == architecture

  def _WritePackageDescriptorToFile(self, package_name, version):
    """Write out the packages to be analysed."""
    package_pb = wheelbarrow_pb2.Package()
    package_pb.name = package_name
    package_pb.architecture = version.architecture
    package_pb.version = version.version
    package_pb.status = wheelbarrow_pb2.Package.AVAILABLE
    file_name = '%s-%s-%s' % (package_name, version.version,
                              version.architecture)
    path = os.path.join(self._host_nfs_share, NfsAnalysisSetupAgent.INPUT_DIR,
                        file_name)
    if utils.WriteProtobufToFile(package_pb, path, self._text_output, True):
      return True
    else:
      logging.error('Could not write package descriptor to file %s.', path)
      return False

  def _SetUpConfigFile(self):
    """Set up a configuration file to be read by guests.

    Returns:
      True if all goes well.
    """

    logging.info('Setting up config file...')
    config = wheelbarrow_pb2.NfsAnalysisConfig()
    config.input_dir = os.path.join(self._guest_nfs_share,
                                    NfsAnalysisSetupAgent.INPUT_DIR)
    config.output_dir = os.path.join(self._guest_nfs_share,
                                     NfsAnalysisSetupAgent.OUTPUT_DIR)
    config.log_dir = os.path.join(self._guest_nfs_share,
                                  NfsAnalysisSetupAgent._LOG_DIR)
    config.text_output = self._text_output
    # We estimate that the VM startup and initial setup should take less than a
    # minute.
    config.timeout = self._timeout - 60
    config_file_path = os.path.join(self._host_nfs_share,
                                    NfsAnalysisSetupAgent.CONFIG_FILE_NAME)
    if utils.WriteProtobufToFile(config, config_file_path, False):
      return True
    else:
      logging.error('Error while writing config file %s.', config_file_path)
      return False
