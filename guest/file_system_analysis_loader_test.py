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
"""Tests for AnalysisLoader class."""

import glob
import logging
import os.path
import mox
import sys
import unittest
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from google.protobuf import text_format

from common import wheelbarrow_pb2
from guest import analysis_loader
from guest import file_system_analysis_loader as fs_loader
from guest.analysis_loader import AnalysisLoadingError
from guest.analyzers.analyzer import Analyzer


class MockAnalyzer(Analyzer):
  pass


class MockRandomClass(object):
  pass


class AnalysisLoaderTest(unittest.TestCase):
  def setUp(self):
    self.test_pattern = 'test_pattern'
    self.test_file_name = 'test_file_name'
    self.expected_triggers = set([wheelbarrow_pb2.EXTRACT,
                                  wheelbarrow_pb2.RUN_BINARIES])
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(logging, 'warning')
    self.mox.StubOutWithMock(logging, 'error')
    self.mox.StubOutWithMock(glob, 'glob')
    self.mox.StubOutWithMock(analysis_loader.AnalysisLoader,
                             '_GetTriggersFromDescriptor')
    self.mox.StubOutWithMock(analysis_loader.AnalysisLoader,
                             '_GetInstanceByClassName')

  def testLoadAnalysesWithGoodFileName(self):
    self.mox.StubOutWithMock(fs_loader.FileSystemAnalysisLoader,
                             '_ParseAnalysisDescriptor')
    glob.glob(self.test_pattern).AndReturn([self.test_file_name])
    expected_descriptor = self._CreateExpectedDescriptor('mock_analyzer')
    fs_loader.FileSystemAnalysisLoader._ParseAnalysisDescriptor(
        self.test_file_name).AndReturn(expected_descriptor)
    analysis_loader.AnalysisLoader._GetTriggersFromDescriptor(
        expected_descriptor).AndReturn(self.expected_triggers)
    expected_analyzer = analysis_loader.AnalysisLoader._GetInstanceByClassName(
        'mock_analyzer').AndReturn(MockAnalyzer())
    self.mox.ReplayAll()

    loader = fs_loader.FileSystemAnalysisLoader([self.test_pattern])
    analyses = loader.LoadAnalyses()
    self.assertEqual(len(analyses), 1)
    str1 = text_format.MessageToString(analyses[0]._descriptor, as_one_line=True)
    str2 = text_format.MessageToString(expected_descriptor, as_one_line=True)
    self.assertEqual(str1, str2)
    self.assertEqual(analyses[0]._triggers, self.expected_triggers)
    self.assertEqual(analyses[0]._module, expected_analyzer)
    self.mox.VerifyAll()

  def testLoadAnalysesWithGlobProblem(self):
    glob.glob(self.test_pattern).AndRaise(AnalysisLoadingError)
    """logging.error('Unable to get descriptor file names by globbing %s: %s',
                  self.test_pattern, mox.IgnoreArg())"""
    self.mox.ReplayAll()

    loader = fs_loader.FileSystemAnalysisLoader([self.test_pattern])
    self.assertRaises(AnalysisLoadingError, loader.LoadAnalyses)
    self.mox.VerifyAll()

  def testLoadAnalysesWithDescriptorParsingProblem(self):
    self.mox.StubOutWithMock(fs_loader.FileSystemAnalysisLoader,
                             '_ParseAnalysisDescriptor')
    glob.glob(self.test_pattern).AndReturn([self.test_file_name])
    fs_loader.FileSystemAnalysisLoader._ParseAnalysisDescriptor(
        self.test_file_name).AndReturn(None)
    logging.error('Failed to parse descriptor from file %s',
                  self.test_file_name)
    self.mox.ReplayAll()

    loader = fs_loader.FileSystemAnalysisLoader([self.test_pattern])
    analyses = loader.LoadAnalyses()
    self.assertEquals(len(analyses), 0)
    self.mox.VerifyAll()

  def testLoadAnalysesWithAnalyzerInstantiationProblem(self):
    self.mox.StubOutWithMock(fs_loader.FileSystemAnalysisLoader,
                             '_ParseAnalysisDescriptor')
    glob.glob(self.test_pattern).AndReturn([self.test_file_name])
    non_existent_analyzer = 'BadClass'
    expected_descriptor = self._CreateExpectedDescriptor(non_existent_analyzer)
    fs_loader.FileSystemAnalysisLoader._ParseAnalysisDescriptor(
        self.test_file_name).AndReturn(expected_descriptor)
    analysis_loader.AnalysisLoader._GetTriggersFromDescriptor(
        expected_descriptor).AndReturn(self.expected_triggers)
    logging.error('Could not instantiate %s: %s', non_existent_analyzer,
                  mox.IgnoreArg())
    analysis_loader.AnalysisLoader._GetInstanceByClassName(
        non_existent_analyzer).AndRaise(AnalysisLoadingError)
    self.mox.ReplayAll()

    loader = fs_loader.FileSystemAnalysisLoader([self.test_pattern])
    analyses = loader.LoadAnalyses()
    self.assertEquals(len(analyses), 0)
    self.mox.VerifyAll()

  def testLoadAnalysesWithNonAnalyzerModule(self):
    self.mox.StubOutWithMock(fs_loader.FileSystemAnalysisLoader,
                             '_ParseAnalysisDescriptor')
    glob.glob(self.test_pattern).AndReturn([self.test_file_name])
    non_analyzer_module = 'mock_random_class'
    expected_descriptor = self._CreateExpectedDescriptor(non_analyzer_module)
    fs_loader.FileSystemAnalysisLoader._ParseAnalysisDescriptor(
        self.test_file_name).AndReturn(expected_descriptor)
    analysis_loader.AnalysisLoader._GetTriggersFromDescriptor(
        expected_descriptor).AndReturn(self.expected_triggers)
    analysis_loader.AnalysisLoader._GetInstanceByClassName(
        non_analyzer_module).AndReturn(MockRandomClass())
    logging.error('%s is not an Analyzer in analysis %s', non_analyzer_module,
                  self.test_file_name)
    self.mox.ReplayAll()

    loader = fs_loader.FileSystemAnalysisLoader([self.test_pattern])
    analyses = loader.LoadAnalyses()
    self.assertEquals(len(analyses), 0)
    self.mox.VerifyAll()

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()

  def _CreateExpectedDescriptor(self, analyzer):
    expected_descriptor = wheelbarrow_pb2.AnalysisDescriptor()
    expected_descriptor.name = 'test_name'
    expected_descriptor.description = 'test_description'
    expected_descriptor.category = 'test_category'
    expected_descriptor.module = analyzer
    return expected_descriptor

if __name__ == '__main__':
  unittest.main()
