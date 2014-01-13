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
"""Binary launcher."""

import logging
import os
import re
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from common.timed_subprocess import TimedSubprocess
from guest.analyzers.file_analyzer import FileAnalyzer


class BinaryLauncher(object):
  """A class to launch package binaries."""

  _EXEC_EXPRESSION = re.compile(r'exec[lv][ep]?\(\"([^\"]*)\".*\)')

  def __init__(self, service_manager):
    self._service_manager = service_manager

  def RunBinaries(self, timeout=60):
    """Run binaries contained in an application package.

    Args:
      timeout: The maximum duration that each binary should run.
    """

    # Add leading slash to package binary paths, since they are recorded as
    # paths relative to the package extract directory.
    package_binaries = set('/%s' % s for s in FileAnalyzer.GetBinaries())
    excluded_binaries = self._GetExcludedBinaries()
    dev_null = open(os.devnull, 'w')
    for binary in package_binaries - excluded_binaries:
      # Exclude .so files.
      if binary.endswith('.so'):
        continue
      # Launch in a timed subprocess, since this may take arbitrarily long
      # otherwise.
      subproc = TimedSubprocess(timeout)
      if subproc.Popen(BinaryLauncher._MakeBinaryCommand(binary, True),
                       stdout=dev_null, stderr=dev_null):
        if subproc.Wait():
          logging.warning('Binary %s terminated with errors.', binary)
      else:
        logging.warning('Could not start binary %s.', binary)
    dev_null.close()

  @staticmethod
  def _MakeBinaryCommand(binary, sudo=False):
    """Make a command to launch a binary file.

    Args:
      binary: The path to a binary.
      sudo: True if the binary should be run using sudo.

    Returns:
      A command to run a binary, as a list.
    """

    cmd = ['/usr/bin/sudo'] if sudo else []
    cmd.append(binary)
    return cmd

  def _GetExcludedBinaries(self):
    """Get the binaries that should not be run.

    Returns:
      A set of excluded binaries.
    """

    excluded_binaries = set()
    for file_name in self._service_manager.GetStracePaths('start'):
      excluded_binaries |= BinaryLauncher._DetectExecutedBinaries(file_name)
    for file_name in self._service_manager.GetStracePaths('stop'):
      excluded_binaries |= BinaryLauncher._DetectExecutedBinaries(file_name)
    return excluded_binaries

  @staticmethod
  def _DetectExecutedBinaries(file_name):
    """Detect executed binaries from an strace output file.

    Args:
      file_name: An strace output file.

    Returns:
      A set of the binaries executed during an strace run.
    """

    executed_binaries = set()
    try:
      with open(file_name, 'r') as strace_file:
        for line in strace_file:
          match = BinaryLauncher._EXEC_EXPRESSION.search(line)
          if match:
            binary = match.group(1)
            if binary[0] != '/':
              logging.error('Expecting an absolute path to a binary, found %s '
                            'instead.', binary)
            else:
              executed_binaries.add(binary)
        strace_file.close()
        return executed_binaries
    except (IOError, OSError) as err:
      logging.error('Could not read strace file %s: %s', file_name, err)
      return executed_binaries
