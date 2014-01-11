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
"""Analysis descriptor parser test."""

import hashlib
import logging
import mox
import os
import sys
import unittest
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import test_utils
from common import wheelbarrow_pb2
from guest import analysis
from guest.analyzers.file_analyzer import FileAnalyzer


TEST_PATH = 'guest/analyzers_test/test_data'


class FileAnalyzerTest(unittest.TestCase):
  def setUp(self):
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.test_path = 'test_path'
    self.script = os.path.realpath(os.path.join(self.base_dir, 'script'))
    self.mox = mox.Mox()

  def testRunAnalysisWithImplementedPerformAnalysis(self):
    out = 'test'
    trigger = wheelbarrow_pb2.EXTRACT
    self.mox.StubOutWithMock(FileAnalyzer, '_PerformAnalysis')
    file_analyzer = FileAnalyzer()
    file_analyzer._PerformAnalysis(self.script).AndReturn(out)
    self.mox.ReplayAll()

    argument = [(self.script, self.script)]
    file_analyzer.RunAnalysis(trigger, argument, '')
    self.mox.VerifyAll()
    self.assertEqual(
        file_analyzer._GetAnalysisResultForTrigger(trigger)[self.script],
        out)

  def testRunAnalysisWithNotImplementedPerformAnalysis(self):
    argument = [(self.test_path, self.test_path)]
    analyzer = FileAnalyzer()
    self.assertRaises(NotImplementedError, analyzer.RunAnalysis, None, argument,
                      '')

  def testDetermineFileTypeWithBinaryFile(self):
    self.CheckFileType(os.path.join(self.base_dir, 'elf'),
                       wheelbarrow_pb2.FileResult.BINARY)

  def testDetermineFileTypeWithRandomFile(self):
    self.CheckFileType(os.path.join(self.base_dir, 'random_type'),
                       wheelbarrow_pb2.FileResult.OTHER)

  def testDetermineFileTypeWithScript(self):
    self.CheckFileType(self.script, wheelbarrow_pb2.FileResult.SCRIPT)

  def testDetermineFileTypeWithTextFile(self):
    self.CheckFileType(os.path.join(self.base_dir, 'text'),
                       wheelbarrow_pb2.FileResult.TEXT)

  def testDetermineFileTypeWithBadFileName(self):
    file_name = os.path.join(self.base_dir, 'bad_file_name')
    self.mox.StubOutWithMock(logging, 'error')
    logging.error('Could not execute file on %s: %s', file_name,
                  mox.IgnoreArg())
    self.mox.ReplayAll()
    self.assertRaises(analysis.RecoverableAnalysisError,
                      FileAnalyzer._DetermineFileType, file_name)
    self.mox.VerifyAll()

  def testPrepareDiffFileResult(self):
    diff_pair = wheelbarrow_pb2.AnalysisDescriptor.DiffPair()
    diff_pair.before = wheelbarrow_pb2.EXTRACT
    diff_pair.after = wheelbarrow_pb2.INSTALL
    file_analyzer = FileAnalyzer()
    file_analyzer._RecordFileType(self.script, self.test_path)
    pb = file_analyzer._PrepareDiffFileResult(
        self.test_path,
        wheelbarrow_pb2.AnalysisResult(),
        wheelbarrow_pb2.ADD, diff_pair)
    reference_file_path = os.path.join(self.base_dir, 'diff_file_result')
    test_utils.CheckResultProtobufFromFile(self, pb, reference_file_path,
                                           wheelbarrow_pb2.FileResult())

  def testPrepareDescriptiveFileResult(self):
    file_analyzer = FileAnalyzer()
    file_analyzer._RecordFileType(self.script, self.test_path)
    pb = file_analyzer._PrepareDescriptiveFileResult(
        self.test_path,
        wheelbarrow_pb2.AnalysisResult(),
        wheelbarrow_pb2.REMOVE)
    reference_file_path = os.path.join(self.base_dir, 'descriptive_file_result')
    test_utils.CheckResultProtobufFromFile(self, pb, reference_file_path,
                                           wheelbarrow_pb2.FileResult())

  def testPrepareFileResultWithBadArguments(self):
    self.assertRaises(analysis.FatalAnalysisError,
                      FileAnalyzer()._PrepareFileResult, self.test_path,
                      wheelbarrow_pb2.AnalysisResult(),
                      wheelbarrow_pb2.ADD, None, None)

  def testComputeStringHash(self):
    reference_file_path = os.path.join(self.base_dir, 'descriptive_file_result')
    reference_file = open(reference_file_path)
    test_string = reference_file.read()
    reference_hash = ('2632833731b11b9c9e0f071209e29e8cce04e900f89404f251654921'
                      '355728dc')
    test_hash = FileAnalyzer._ComputeStringHash(test_string, hashlib.sha256)
    self.assertEqual(test_hash, reference_hash)

  def CheckFileType(self, file_name, file_type):
    file_name = os.path.realpath(file_name)
    self.assertEqual(FileAnalyzer()._DetermineFileType(file_name), file_type)

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()


if __name__ == '__main__':
  unittest.main()
