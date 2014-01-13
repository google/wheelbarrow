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
"""The service manager."""

import atexit
import itertools
import glob
import logging
import os.path
import shutil
import sys
import tempfile

WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common.timed_subprocess import TimedSubprocess
from guest import guest_utils
from guest.triggers import TriggerError


class ServiceManager(object):
  """This class manages actions performed with services."""

  _SERVICE = '/usr/sbin/service'
  _SERVICE_LINE = r' \[ . \]  (.+)'

  def __init__(self):
    self._strace_dir = None

  def RecordServices(self):
    """Record the services installed on the system."""

    self._services = ServiceManager._DetermineServiceList()

  def RecordNewServices(self):
    """Record the new services on the system.

    RecordServices() should be called before this method.
    """

    new_service_list = ServiceManager._DetermineServiceList()
    self._new_services = new_service_list - self._services

  def StartNewServices(self, strace=False):
    """Start the services that were detected as new.

    This should be called after RecordServices() and RecordNewServices().

    Args:
      strace: True if strace should be run on the service start.
    """

    for service in self._new_services:
      logging.info('Starting service %s...', service)
      self._PerformServiceAction(service, 'start', strace)

  def StopNewServices(self, strace=False):
    """Stop the services that were detected as new.

    This should be called after RecordServices() and RecordNewServices().

    Args:
      strace: True if strace should be run on the service stop.
    """

    for service in self._new_services:
      logging.info('Stopping service %s...', service)
      self._PerformServiceAction(service, 'stop', strace)

  def GetStracePaths(self, action):
    """Get the path to files containing the strace of a service action.

    This returns something useful only if you have run StartNewServices() and/or
    StopNewServices() with strace=True before.

    Args:
      action: A service action.

    Returns:
      A list of paths to the strace files for the requested action.
    """

    if not self._strace_dir:
      return []
    return glob.glob('%s_*' % os.path.join(self._strace_dir, action))

  def _PerformServiceAction(self, service, action, strace):
    """Perform an action (e.g., start) on a service.

    This function optionally runs the service action using strace. The strace
    output is directed to a file because we do not want stderr to be polluted
    by the strace output.

    Args:
      service: The name of a service.
      action: The service action.
      strace: True if strace output is desired.
    """

    cmd = []
    if strace:
      strace_file = os.path.join(self._GetStraceDir(),
                                 '%s_%s' % (action, service))
      cmd = ['strace', '-o', strace_file, '-f']
    cmd += [ServiceManager._SERVICE, service, action]
    try:
      subproc = TimedSubprocess(120)
      subproc.Popen(cmd)
      returncode = subproc.Wait()
      if returncode:
        logging.error('Could not perform %s on service %s: return code %d',
                      action, service, returncode)
    except (OSError, ValueError) as e:
      logging.error('Could not perform %s on service %s: %s',
                    action, service, e)

  def _GetStraceDir(self):
    if not self._strace_dir:
      self._strace_dir = tempfile.mkdtemp()
      atexit.register(shutil.rmtree, self._strace_dir)
    return self._strace_dir

  @staticmethod
  def _DetermineServiceList():
    """Determine the list of services.

    Returns:
      A set of services.

    Raises:
      TriggerError: If something goes wrong with the services command.
    """

    try:
      cmd = [ServiceManager._SERVICE, '--status-all']
      # This returns a list of lists, where each nested list has a single
      # element, which is the name of a service.
      services = guest_utils.ExecuteCommandAndMatch(
          cmd, ServiceManager._SERVICE_LINE)
      # Flatten the list of lists to a set before returning it.
      return set(itertools.chain.from_iterable(services))
    except guest_utils.CommandMatchingError as e:
      error = 'Could not determine services: %s' % str(e)
      logging.error(error)
      raise TriggerError(error)
