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
"""A Debian "extract" trigger."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

import atexit
import os
import shutil
import tempfile
import time

import apt
import apt_inst
import apt_pkg

import logging

from guest import triggers
from guest.binary_launcher import BinaryLauncher
from guest.service_manager import ServiceManager


class DebExtract(triggers.Extract):
  """A Debian "extract" trigger."""

  def __init__(self, package_path, package_extract_dir):
    """Constructor.

    Args:
      package_path: The path to the archive of the application package under
                    test.
      package_extract_dir: The directory to which the package should be
                           extracted.
    """

    self._package_path = package_path
    self._package_extract_dir = package_extract_dir

  def RunTrigger(self):
    logging.info('Extracting...')
    try:
      package_file = open(self._package_path)
      apt_inst.debExtractArchive(package_file, self._package_extract_dir)
      package_file.close()
    except (IOError, SystemError) as e:
      error = ('Could not open and extract application package %s: %s'
               % (self._package_path, str(e)))
      logging.error(error)
      raise triggers.TriggerError(error)


class DebInstall(triggers.Install):
  """A Debian "install" trigger."""

  def __init__(self, cache, package, service_manager):
    """Constructor.

    Args:
      cache: An apt cache.
      package: A package to be installed.
      service_manager: A service manager for the application.
    """

    self._cache = cache
    self._package = package
    self._service_manager = service_manager

  def RunTrigger(self):
    """Run a Debian "install" trigger.

    This trigger first records services present on the system, then installs the
    package under test, and finally records the newly installed services.

    Raises:
      triggers.TriggerError if the package cannot be installed.
    """

    self._service_manager.RecordServices()
    try:
      self._package.mark_install(True, True, False)
      logging.info('Installing...')
      self._cache.commit()
    except (apt.cache.FetchFailedException, SystemError) as e:
      logging.error('Could not install package %s: %s', self._package.name, e)
      raise triggers.TriggerError('Could not install package %s: %s'
                                  % (self._package.name, str(e)))
    self._service_manager.RecordNewServices()


class DebRemove(triggers.Trigger):
  """A generic Debian "remove"/"purge" trigger.

  In apt, "purge" is an option for the "remove" call. However, "remove" and
  "purge" are two different triggers. This class implements a generic
  "remove"/"purge". Instantiate it or subclass it as appropriate if you want
  "remove" or "purge" behavior.
  """

  def __init__(self, cache, package, purge, message):
    """Constructor.

    Args:
      cache: An apt cache.
      package: An apt package to be removed.
      purge: True if the package should be purged, False if it should only be
             removed.
      message: A message to be logged before performing the trigger, or None if
               nothing should be logged.
    """

    self._cache = cache
    self._package = package
    self._purge = purge
    self._message = message

  def RunTrigger(self):
    self._cache.open(None)
    try:
      self._package.mark_delete(True, self._purge)
      if self._message:
        logging.info(self._message)
      self._cache.commit()
    except SystemError as e:
      error = ('Could not remove or purge package %s: %s'
               % (self._package.name, str(e)))
      logging.error(error)
      raise triggers.TriggerError(error)


class DebRemoveNoPurge(triggers.Remove, DebRemove):
  """A Debian "remove" trigger."""

  def __init__(self, cache, package):
    super(DebRemoveNoPurge, self).__init__(cache, package, False, 'Removing...')


class DebRemoveWithPurge(triggers.Purge, DebRemove):
  """A Debian "purge" trigger."""

  def __init__(self, cache, package):
    super(DebRemoveWithPurge, self).__init__(cache, package, True, 'Purging...')


class DebStartService(triggers.StartService):
  """A Debian "start service" trigger."""

  def __init__(self, service_manager):
    """Constructor.

    Args:
      service_manager: A service manager for the application.
    """

    self._service_manager = service_manager

  def RunTrigger(self):
    logging.info('Starting services...')
    self._service_manager.StartNewServices(True)


class DebStopService(triggers.StartService):
  """A Debian "stop service" trigger."""

  def __init__(self, service_manager):
    """Constructor.

    Args:
      service_manager: A service manager for the application.
    """
    self._service_manager = service_manager

  def RunTrigger(self):
    logging.info('Stopping services...')
    self._service_manager.StopNewServices(True)


class DebRunBinaries(triggers.RunBinaries):
  """A Debian "run binaries" trigger."""

  def __init__(self, service_manager):
    """Constructor.

    Args:
      service_manager: A service manager for the application.
    """
    self._service_manager = service_manager

  def RunTrigger(self):
    launcher = BinaryLauncher(self._service_manager)
    launcher.RunBinaries()


class DebTriggerManager(triggers.TriggerManager):
  """Debian trigger manager."""

  def SetUpTriggersAndMetadata(self, package_descriptor):
    """Set up the Debian trigger manager.

    Create necessary temporary directories, retrieve package and set up
    triggers.

    Args:
      package_descriptor: The Package() message for the application under test.
    """

    (package_dir, package_extract_dir) = DebTriggerManager._CreateTempDirs(
        package_descriptor)
    cache = self._FetchPackage(package_dir, package_descriptor)
    package_path = self._GetLocalPackagePath(package_dir)
    self._SetMetadata(package_descriptor)
    triggers.TriggerManager._SetPackageExtractDir(package_extract_dir)

    service_manager = ServiceManager()
    # Initialize triggers
    self._triggers = [DebExtract(package_path, package_extract_dir),
                      DebInstall(cache, self._package, service_manager),
                      DebStopService(service_manager),
                      DebStartService(service_manager),
                      DebRunBinaries(service_manager),
                      DebRemoveNoPurge(cache, self._package),
                      DebRemoveWithPurge(cache, self._package)]
    self._trigger_iter = iter(self._triggers)

  def _GetNextTrigger(self):
    try:
      return self._trigger_iter.next()
    except StopIteration:
      raise triggers.NoNextTrigger

  def _SetMetadata(self, package_descriptor):
    package_descriptor.section = self._version.section
    package_descriptor.description = self._version.raw_description
    package_descriptor.analysis_start = int(time.time())

  @staticmethod
  def _CreateTempDirs(package_descriptor):
    """Create temporary directories for the package and the package extraction.

    Args:
      package_descriptor: A wheelbarrow_pb2.Package.

    Returns:
      The created directories.
    """

    package_dir = tempfile.mkdtemp(package_descriptor.name)
    atexit.register(shutil.rmtree, package_dir)
    package_extract_dir = tempfile.mkdtemp('%s-extract'
                                           % package_descriptor.name)
    atexit.register(shutil.rmtree, package_extract_dir)
    return (package_dir, package_extract_dir)

  def _FetchPackage(self, package_dir, package_descriptor):
    """Fetch the package of the application under test.

    Args:
      package_dir: The destination directory for the fetched package.
      package_descriptor: A wheelbarrow_pb2.Package for the package to be
                         fetched.

    Returns:
      The apt cache.

    Raises:
      triggers.TriggerError if the package cannot be fetched.
    """

    apt_pkg.init()
    architecture = package_descriptor.architecture.encode('utf8')
    apt_pkg.config['Apt::Architecture'] = architecture

    self._version = None

    cache = apt.Cache()
    cache.update()
    cache.open(None)
    try:
      self._package = cache[package_descriptor.name]
    except KeyError:
      error = ('No package named %s was found in the apt cache.'
               % package_descriptor.name)
      logging.error(error)
      raise triggers.TriggerError(error)
    for version in self._package.versions:
      if (version.version == package_descriptor.version
          and version.architecture == architecture):
        try:
          version.fetch_binary(package_dir)
          self._package.candidate = version
          self._version = version
          break
        except apt.package.FetchError as e:
          error = ('Could not fetch package %s-%s-%s: %s'
                   % (package_descriptor.name, package_descriptor.version,
                      architecture, str(e)))
          logging.error(error)
          raise triggers.TriggerError(error)

    if not self._version:
      error = ('No package was found when looking for %s-%s-%s.'
               % (package_descriptor.name, package_descriptor.version,
                  architecture))
      logging.error(error)
      raise triggers.TriggerError(error)
    return cache

  def _GetLocalPackagePath(self, package_dir):
    """Get the local path to the Debian package.

    There should only be one file in there, but still check, just in case
    something strange happened.

    Args:
      package_dir: The directory which contains the Debian package.

    Returns:
      The path to the Debian package.

    Raises:
      triggers.TriggerError if the fetch directory does not contain exactly one
      file.
    """

    dir_contents = os.listdir(package_dir)
    absolute_paths = []
    for item in dir_contents:
      file_name = os.path.join(package_dir, item)
      if os.path.isfile(file_name):
        absolute_paths.append(file_name)
    if len(absolute_paths) != 1:
      raise triggers.TriggerError('Bad contents of package fetch directory: %s',
                                  absolute_paths)
    return absolute_paths[0]
