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
"""Permission analyzer test."""

import os.path
import shutil
import sys
import time
import tempfile
import unittest
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from collections import Counter
from common import test_utils
from common import wheelbarrow_pb2
from guest.analyzers import inotify_file_analyzer


TEST_PATH = 'guest/analyzers_test/test_data'
TMP_PATH = tempfile.gettempdir()


class InotifyFileAnalyzerTest(unittest.TestCase):
  def setUp(self):
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.test_file_name = 'permission_analyzer_diff_results'
    self.test_path = os.path.join(self.base_dir, self.test_file_name)
    self.tmp_dir = os.path.join(TMP_PATH, 'inotify_manager')
    shutil.rmtree(self.tmp_dir, ignore_errors=True)
    os.mkdir(self.tmp_dir)
    self.trigger1 = wheelbarrow_pb2.EXTRACT
    self.trigger2 = wheelbarrow_pb2.INSTALL
    self.trigger3 = wheelbarrow_pb2.RUN_BINARIES

  def testRunAnalysis(self):
    file_analyzer = inotify_file_analyzer.InotifyFileReadModifyMoveAnalyzer()
    argument = (self.test_path, self.test_path)
    file_analyzer.RunAnalysis(self.trigger1, [argument], None)
    InotifyFileAnalyzerTest._GenerateOpenAndAccessEvents(self.test_path, 1)
    file_analyzer.RunAnalysis(self.trigger2, [argument], None)
    argument2 = (self.base_dir, self.base_dir)
    file_analyzer.RunAnalysis(self.trigger2, [argument2], None)
    InotifyFileAnalyzerTest._GenerateOpenAndAccessEvents(self.test_path, 9)
    time.sleep(1)
    file_analyzer.RunAnalysis(self.trigger3, [argument], None)
    snapshot1 = file_analyzer._GetAnalysisResultForTrigger(self.trigger1)
    snapshot2 = file_analyzer._GetAnalysisResultForTrigger(self.trigger2)
    snapshot3 = file_analyzer._GetAnalysisResultForTrigger(self.trigger3)
    self.assertNotIn(self.test_path, snapshot1)
    self._CheckCounterResult(snapshot2, self.test_path, 1)
    self._CheckCounterResult(snapshot3, self.test_path, 20)

  def testAddDiffResults(self):
    reference_file_name = os.path.join(
        WHEELBARROW_HOME, TEST_PATH, 'inotify_file_analyzer_diff_results')
    file_analyzer = inotify_file_analyzer.InotifyFileAnalyzer()
    file_analyzer._file_types = {
        'file1': wheelbarrow_pb2.FileResult.TEXT,
        'file2': wheelbarrow_pb2.FileResult.SCRIPT}
    result1 = Counter({'file1': 2})
    result2 = Counter({'file1': 5, 'file2': 21})
    file_analyzer._analysis_results[self.trigger1] = result1
    file_analyzer._analysis_results[self.trigger3] = result2
    analysis_result = wheelbarrow_pb2.AnalysisResult()
    analysis_result.analysis_name = 'test'
    diff_pair = wheelbarrow_pb2.AnalysisDescriptor.DiffPair()
    diff_pair.before = self.trigger1
    diff_pair.after = self.trigger3
    file_analyzer.AddDiffResults(diff_pair, analysis_result)
    test_utils.CheckResultProtobufFromFile(
        self, analysis_result, reference_file_name,
        wheelbarrow_pb2.AnalysisResult())

  def testGetEventNames(self):
    file_analyzer = inotify_file_analyzer.InotifyFileAnalyzer()
    self.assertRaises(NotImplementedError, file_analyzer._GetEventNames)

  def _CheckCounterResult(self, counter, key, count):
    self.assertIn(key, counter)
    self.assertEqual(counter[key], count)

  @staticmethod
  def _GenerateOpenAndAccessEvents(file_path, count=1):
    for _ in range(count):
      test_file = open(file_path)
      test_file.read()
      test_file.close()
      # Waiting a bit, since it seems that inotify may coalesce identical events
      # received in a short time.
      # See http://www.cs.princeton.edu/~sapanb/inotify_missing_events.html and
      # http://stackoverflow.com/a/17610077
      time.sleep(0.001)


if __name__ == '__main__':
  unittest.main()
