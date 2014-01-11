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
"""Network listener analyzer test."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


import subprocess


import mox
import gflags
import unittest


from common import test_utils
from common import wheelbarrow_pb2
from guest import guest_utils
from guest.analysis import RecoverableAnalysisError
from guest.analyzers.file_analyzer import FileAnalyzer
from guest.analyzers.network_listener_analyzer import NetworkListenerAnalyzer


FLAGS = gflags.FLAGS
TEST_PATH = 'guest/test_data'
ANALYZER_TEST_PATH = 'guest/analyzers_test/test_data'


class NetworkListenerAnalyzerTest(unittest.TestCase):
  def setUp(self):
    self.base_dir1 = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.base_dir2 = os.path.join(WHEELBARROW_HOME, ANALYZER_TEST_PATH)
    self.binaries = set(['usr/sbin/cupsd', 'bin/ls', 'usr/sbin/inetd'])
    self.expected_result = {wheelbarrow_pb2.RUN_BINARIES:
                            [['tcp', '0.0.0.0', '21', '0.0.0.0', '*', 'LISTEN',
                              '2769', '/usr/sbin/inetd'],
                             ['tcp', '127.0.0.1', '631', '0.0.0.0', '*',
                              'LISTEN', '697', '/usr/sbin/cupsd'],
                             ['tcp6', '::1', '631', '::', '*', 'LISTEN', '697',
                              '/usr/sbin/cupsd']]}

    self.mox = mox.Mox()

  def testRunAnalysisWithSuccess(self):
    self.mox.StubOutWithMock(subprocess, 'check_output')
    self.mox.StubOutWithMock(FileAnalyzer, 'GetBinaries')
    netstat_out = self.LoadNetstatOut()
    subprocess.check_output(NetworkListenerAnalyzer._NETSTAT_COMMAND,
                            stderr=subprocess.STDOUT).AndReturn(netstat_out)
    FileAnalyzer.GetBinaries().AndReturn(self.binaries)
    ps_path = os.path.join(self.base_dir1, 'ps_aux')
    ps_file = open(ps_path)
    ps_out = ps_file.read()
    ps_file.close()
    subprocess.check_output(
        guest_utils._PS_COMMAND, stderr=subprocess.STDOUT).AndReturn(ps_out)
    self.mox.ReplayAll()

    analyzer = NetworkListenerAnalyzer()
    analyzer.RunAnalysis(wheelbarrow_pb2.RUN_BINARIES, None, None)
    self.assertEqual(analyzer._analysis_results, self.expected_result)

  def testRunAnalysisWithNetstatFailure(self):
    self.mox.StubOutWithMock(guest_utils, 'ExecuteCommandAndMatch')
    guest_utils.ExecuteCommandAndMatch(
        NetworkListenerAnalyzer._NETSTAT_COMMAND,
        NetworkListenerAnalyzer._LISTEN_EXPRESSION).AndRaise(
            RecoverableAnalysisError)
    self.mox.ReplayAll()

    analyzer = NetworkListenerAnalyzer()
    self.assertRaises(RecoverableAnalysisError, analyzer.RunAnalysis,
                      wheelbarrow_pb2.RUN_BINARIES, None, None)
    self.mox.VerifyAll()

  def testRunAnalysisWithPsFailure(self):
    self.mox.StubOutWithMock(subprocess, 'check_output')
    self.mox.StubOutWithMock(FileAnalyzer, 'GetBinaries')
    self.mox.StubOutWithMock(guest_utils, 'FindPidsForBinaries')
    netstat_out = self.LoadNetstatOut()
    subprocess.check_output(NetworkListenerAnalyzer._NETSTAT_COMMAND,
                            stderr=subprocess.STDOUT).AndReturn(netstat_out)
    FileAnalyzer.GetBinaries().AndReturn(self.binaries)
    guest_utils.FindPidsForBinaries(
        set('/%s' % s for s in self.binaries)).AndRaise(
            RecoverableAnalysisError)
    self.mox.ReplayAll()

    analyzer = NetworkListenerAnalyzer()
    self.assertRaises(RecoverableAnalysisError, analyzer.RunAnalysis,
                      wheelbarrow_pb2.RUN_BINARIES, None, None)
    self.mox.VerifyAll()

  def testAddDescriptiveResults(self):
    reference_file_path = os.path.join(
        self.base_dir2, 'network_listener_analyzer_descriptive_results')
    analyzer = NetworkListenerAnalyzer()
    analyzer._analysis_results = self.expected_result
    analysis_result = wheelbarrow_pb2.AnalysisResult()
    analysis_result.analysis_name = 'test'
    analyzer.AddDescriptiveResults(wheelbarrow_pb2.RUN_BINARIES,
                                   analysis_result)
    test_utils.CheckResultProtobufFromFile(
        self, analysis_result, reference_file_path,
        wheelbarrow_pb2.AnalysisResult())

  def LoadNetstatOut(self):
    netstat_path = os.path.join(self.base_dir2, 'netstat_anp')
    netstat_file = open(netstat_path)
    netstat_out = netstat_file.read()
    netstat_file.close()
    return netstat_out

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()


if __name__ == '__main__':
  unittest.main()
