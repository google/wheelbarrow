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
"""Guest utility functions test."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)



import os.path
import subprocess
import unittest
import mox


from guest import guest_utils


TEST_PATH = 'guest/test_data'


class GuestUtilsTest(unittest.TestCase):
  def setUp(self):
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.test_file_name = 'ps_aux'
    self.test_path = os.path.join(self.base_dir, self.test_file_name)
    self.bad_cmd = [os.path.join(self.base_dir, 'ls')]

    self.mox = mox.Mox()

  def testExecuteCommandAndMatchWithResults(self):
    cmd = ['ls', '-lL', self.base_dir]
    pattern = r'(?:\S+\s+){4}(\S+)\s+(?:\S+\s+){3}(\S+).*'

    expected_result = [('6814', 'ps_aux'), ('364', 'strace_bad_binary'),
                       ('980', 'strace_start'), ('320', 'strace_stop')]
    result = guest_utils.ExecuteCommandAndMatch(cmd, pattern)
    self.assertEquals(result, expected_result)

  def testExecuteCommandAndMatchWithNoResults(self):
    cmd = ['ls', self.base_dir]
    pattern = r'(?:\S+\s+){4}(\S+)\s+(?:\S+\s+){3}(\S+).*'

    expected_result = []
    result = guest_utils.ExecuteCommandAndMatch(cmd, pattern)
    self.assertEquals(result, expected_result)

  def testExecuteCommandAndMatchWithError(self):
    self.assertRaises(guest_utils.CommandMatchingError,
                      guest_utils.ExecuteCommandAndMatch, self.bad_cmd, r'.*')

  def testFindPidsForBinariesWithSuccess(self):
    self.mox.StubOutWithMock(subprocess, 'check_output')
    ps_aux_file = open(self.test_path)
    ps_aux_out = ps_aux_file.read()
    ps_aux_file.close()
    subprocess.check_output(
        guest_utils._PS_COMMAND, stderr=subprocess.STDOUT).AndReturn(ps_aux_out)
    self.mox.ReplayAll()

    expected_result = {'1': '/sbin/init', '697': '/usr/sbin/cupsd',
                       '2769': '/usr/sbin/inetd'}
    binaries = set(['/sbin/init', '/usr/sbin/cupsd', '/usr/sbin/inetd',
                    '/bin/ls', '/usr/bin/man'])
    result = guest_utils.FindPidsForBinaries(binaries)
    self.assertEqual(result, expected_result)
    self.mox.VerifyAll()

  def testFindPidsForBinariesWithError(self):
    self.mox.StubOutWithMock(guest_utils, 'ExecuteCommandAndMatch')
    pattern = r'\S+\s+(\d+)(?:\s+\S+){8}\s+(\S+).*'
    guest_utils.ExecuteCommandAndMatch(
        guest_utils._PS_COMMAND, pattern).AndRaise(
            guest_utils.CommandMatchingError)
    self.mox.ReplayAll()

    self.assertRaises(guest_utils.PidMatchingError,
                      guest_utils.FindPidsForBinaries, set())
    self.mox.VerifyAll()

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()


if __name__ == '__main__':
  unittest.main()
