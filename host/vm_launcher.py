#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Author: octeau@cs.psu.edu (Damien Octeau)
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
"""VM management."""


import logging
import os.path
import sys

WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)
from common.timed_subprocess import TimedSubprocess


def StartVm(cmd, timeout):
  """Start a VM with timeout.

  Args:
    cmd: A command to execute.
    timeout: The timeout after which the VM should be terminated.

  Returns:
    True if the VM executed without any errors.
  """

  vm = TimedSubprocess(timeout)
  if vm.Popen(cmd):
    logging.info('VM process was successfully started.')
    if vm.Wait():
      logging.error('VM process has terminated with errors.')
      return False
    else:
      logging.info('VM process has terminated without errors.')
      return True
  else:
    logging.error('VM process was not started.')
    return False


def MakeVmCommand(image, memory, snapshot):
  """Make a command to start a QEMU VM.

  Args:
    image: The path to a QEMU VM image.
    memory: The amount of memory to be reserved for the VM.
    snapshot: True if the VM should be started in snapshot mode.

  Returns:
    A command to start a VM, as a list of strings.
  """

  cmd = ['qemu-system-x86_64',
         '-hda', image,
         '-m', str(memory)]
  # Concatenate any additional options.
  if snapshot:
    cmd += ['-snapshot']
  return cmd
