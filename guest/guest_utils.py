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
"""Guest utility functions."""

import os.path
import re
import subprocess
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


class Error(Exception):
  pass


class CommandMatchingError(Error):
  pass


class PidMatchingError(Error):
  pass


_PS = '/bin/ps'
_PS_COMMAND = [_PS, 'aux']


def ExecuteCommandAndMatch(cmd, pattern):
  """Execute a shell command and match the output with a pattern.

  Args:
    cmd: A shell command, as a list of strings.
    pattern: A pattern to be matched.

  Returns:
    A list of lists, where each nested list represents the match groups for a
    single line of the shell output.

  Raises:
    CommandMatchingError: If something goes wrong with the command execution.
  """

  out = None
  try:
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
  except (subprocess.CalledProcessError, OSError, ValueError) as err:
    error = 'Could not execute %s: %s' % (' '.join(cmd), str(err))
    raise CommandMatchingError(error)
  lines = out.split('\n')
  compiled_pattern = re.compile(pattern)
  result = []
  for line in lines:
    if line:
      match = compiled_pattern.match(line)
      if match:
        result.append(match.groups())
  return result


def FindPidsForBinaries(binaries):
  """Find the PIDs for a set of binaries.

  Args:
    binaries: A set of paths to binaries.

  Returns:
    A dictionary mapping PIDs (as strings) to process paths.

  Raises:
    PidMatchingError: If something goes wrong when executing the ps aux command.
  """

  pid_to_path_map = {}
  pattern = r'\S+\s+(\d+)(?:\s+\S+){8}\s+(\S+).*'
  try:
    for match in ExecuteCommandAndMatch(_PS_COMMAND, pattern):
      if match[1] in binaries:
        pid_to_path_map[match[0]] = match[1]
  except CommandMatchingError as e:
    error = 'Could not compute PID map: %s' % str(e)
    raise PidMatchingError(error)
  return pid_to_path_map
