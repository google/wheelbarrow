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
"""Binary launcher test."""

import logging
import mox
import os.path
import sys
import unittest
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from guest.analyzers.file_analyzer import FileAnalyzer
from guest.binary_launcher import BinaryLauncher

TEST_PATH = 'guest/test_data'


class MockServiceManager(object):
  def __init__(self, base_dir):
    self._paths = {'start': [os.path.realpath(os.path.join(base_dir,
                                                           'strace_start'))],
                   'stop': [os.path.realpath(os.path.join(base_dir,
                                                          'strace_stop'))]}

  def GetStracePaths(self, action):
    return self._paths[action]


class BinaryLauncherTest(unittest.TestCase):
  def setUp(self):
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(FileAnalyzer, 'GetBinaries')
    self.mox.StubOutWithMock(logging, 'error')

  def testRunBinariesWithGoodBinaries(self):
    binary_launcher = BinaryLauncher(None)
    self.mox.StubOutWithMock(binary_launcher, '_GetExcludedBinaries')
    self.mox.StubOutWithMock(BinaryLauncher, '_MakeBinaryCommand')
    FileAnalyzer.GetBinaries().AndReturn(set(['bin/ls']))
    binary_launcher._GetExcludedBinaries().AndReturn(set())
    BinaryLauncher._MakeBinaryCommand('/bin/ls', True).AndReturn(['/bin/ls'])
    self.mox.ReplayAll()
    binary_launcher.RunBinaries()
    self.mox.VerifyAll()

  def testRunBinariesWithTimeout(self):
    binary_launcher = BinaryLauncher(None)
    self.mox.StubOutWithMock(binary_launcher, '_GetExcludedBinaries')
    self.mox.StubOutWithMock(BinaryLauncher, '_MakeBinaryCommand')
    FileAnalyzer.GetBinaries().AndReturn(set(['bin/sleep']))
    binary_launcher._GetExcludedBinaries().AndReturn(set())
    BinaryLauncher._MakeBinaryCommand('/bin/sleep', True).AndReturn(
        ['/bin/sleep', '5'])
    self.mox.ReplayAll()
    binary_launcher.RunBinaries(1)
    self.mox.VerifyAll()

  def testRunBinariesWithBadBinary(self):
    bad_binary = os.path.join(self.base_dir, 'bad_binary')
    binary_launcher = BinaryLauncher(None)
    self.mox.StubOutWithMock(binary_launcher, '_GetExcludedBinaries')
    self.mox.StubOutWithMock(BinaryLauncher, '_MakeBinaryCommand')
    FileAnalyzer.GetBinaries().AndReturn(set([bad_binary[1:]]))
    binary_launcher._GetExcludedBinaries().AndReturn(set())
    BinaryLauncher._MakeBinaryCommand(bad_binary, True).AndReturn([bad_binary])
    logging.error('Unable to run command %s: %s', [bad_binary], mox.IgnoreArg())
    logging.warning('Could not start binary %s.', bad_binary)
    self.mox.ReplayAll()
    binary_launcher.RunBinaries()
    self.mox.VerifyAll()

  def testMakeBinaryCommandWithSudo(self):
    binary = '/bin/ls'
    cmd = BinaryLauncher._MakeBinaryCommand(binary, True)
    expected_cmd = ['/usr/bin/sudo', '/bin/ls']
    self.assertEqual(cmd, expected_cmd)

  def testMakeBinaryCommandWithoutSudo(self):
    binary = '/bin/ls'
    cmd = BinaryLauncher._MakeBinaryCommand(binary, False)
    expected_cmd = ['/bin/ls']
    self.assertEqual(cmd, expected_cmd)

  def testGetExcludedBinariesWithGoodBinaries(self):
    expected_binaries = set(['/usr/bin/basename', '/usr/local/sbin/start',
                             '/usr/local/bin/start', '/usr/sbin/start',
                             '/usr/bin/start', '/sbin/start'])
    binary_launcher = BinaryLauncher(MockServiceManager(self.base_dir))
    binaries = binary_launcher._GetExcludedBinaries()
    self.assertEqual(binaries, expected_binaries)

  def testDetectExecutedBinariesWithBadFileName(self):
    bad_binary_file_name = os.path.join(self.base_dir, 'strace_bad_binary')
    bad_binary = 'usr/bin/start'
    logging.error('Expecting an absolute path to a binary, found %s instead.',
                  bad_binary)
    self.mox.ReplayAll()
    expected_binaries = set()
    binary_launcher = BinaryLauncher(None)
    binaries = binary_launcher._DetectExecutedBinaries(bad_binary_file_name)
    self.mox.VerifyAll()
    self.assertEqual(binaries, expected_binaries)

  def testDetectExecutedBinariesWithBadBinary(self):
    bad_file_name = os.path.join(self.base_dir, 'bad_file_name')
    logging.error('Could not read strace file %s: %s', bad_file_name,
                  mox.IgnoreArg())
    self.mox.ReplayAll()
    expected_binaries = set()
    binary_launcher = BinaryLauncher(None)
    binaries = binary_launcher._DetectExecutedBinaries(bad_file_name)
    self.mox.VerifyAll()
    self.assertEqual(binaries, expected_binaries)

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()

if __name__ == '__main__':
  unittest.main()
