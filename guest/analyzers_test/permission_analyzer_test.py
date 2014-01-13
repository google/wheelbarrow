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
"""Permission analyzer test."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)



import os.path
import unittest

from common import test_utils
from common import wheelbarrow_pb2
from guest.analyzers.permission_analyzer import PermissionAnalyzer


TEST_PATH = 'guest/analyzers_test/test_data'


class PermissionAnalyzerTest(unittest.TestCase):
  def setUp(self):
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.trigger1 = wheelbarrow_pb2.EXTRACT
    self.trigger2 = wheelbarrow_pb2.INSTALL
    file1 = 'file1'
    file2 = 'file2'
    file3 = 'file3'
    self.result1 = {file1: '0444', file2: '0644'}
    self.result2 = {file2: '0666', file3: '0444'}
    self.file_types = {file1: wheelbarrow_pb2.FileResult.TEXT,
                       file2: wheelbarrow_pb2.FileResult.OTHER,
                       file3: wheelbarrow_pb2.FileResult.SCRIPT}
    self.analysis_name = 'test'

  def testPerformAnalysis(self):
    file_path = os.path.join(self.base_dir,
                             'permission_analyzer_descriptive_results')
    expected_permissions = '0555'
    permission_analyzer = PermissionAnalyzer()
    permissions = permission_analyzer._PerformAnalysis(file_path)
    self.assertEqual(permissions, expected_permissions)

  def testAddDescriptiveResults(self):
    reference_file_name = os.path.join(
        self.base_dir, 'permission_analyzer_descriptive_results')
    permission_analyzer = PermissionAnalyzer()
    permission_analyzer._file_types = self.file_types
    permission_analyzer._AddAnalysisResult(self.trigger1, self.result1)
    analysis_result = wheelbarrow_pb2.AnalysisResult()
    analysis_result.analysis_name = self.analysis_name
    permission_analyzer.AddDescriptiveResults(self.trigger1, analysis_result)
    test_utils.CheckResultProtobufFromFile(self, analysis_result,
                                           reference_file_name,
                                           wheelbarrow_pb2.AnalysisResult())

  def testAddDiffResults(self):
    reference_file_name = os.path.join(
        self.base_dir, 'permission_analyzer_diff_results')
    permission_analyzer = PermissionAnalyzer()
    permission_analyzer._file_types = self.file_types
    permission_analyzer._AddAnalysisResult(self.trigger1, self.result1)
    permission_analyzer._AddAnalysisResult(self.trigger2, self.result2)
    analysis_result = wheelbarrow_pb2.AnalysisResult()
    analysis_result.analysis_name = self.analysis_name
    diff_pair = wheelbarrow_pb2.AnalysisDescriptor.DiffPair()
    diff_pair.before = self.trigger1
    diff_pair.after = self.trigger2
    permission_analyzer.AddDiffResults(diff_pair, analysis_result)
    test_utils.CheckResultProtobufFromFile(self, analysis_result,
                                           reference_file_name,
                                           wheelbarrow_pb2.AnalysisResult())

if __name__ == '__main__':
  unittest.main()
