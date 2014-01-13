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
"""Tests for utils functions."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


import os.path
import shutil


import mox
import unittest
import logging
import tempfile

from google.protobuf import text_format
from google.protobuf.message import EncodeError

from common import utils
from common import wheelbarrow_pb2
from common.test_utils import CheckResultProtobufFromFile


TEST_PATH = 'common/test_data'
TMP_PATH = tempfile.gettempdir()

class UtilsTest(unittest.TestCase):
  def setUp(self):
    #self.base_dir = os.path.join(FLAGS.test_srcdir, TEST_PATH)
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.good_analysis_file = os.path.join(self.base_dir, 'analysis_good')
    self.simple_string_file = os.path.join(self.base_dir, 'simple_string')
    self.tmp_dir = os.path.join(TMP_PATH, 'utils')
    shutil.rmtree(self.tmp_dir, ignore_errors=True)
    os.mkdir(self.tmp_dir)

    self.mox = mox.Mox()
    self.mox.StubOutWithMock(logging, 'warning')
    self.mox.StubOutWithMock(logging, 'error')

  def testLoadFileToStringWithSuccess(self):
    result = utils.LoadFileToString(self.simple_string_file)
    self.assertEqual(result, 'This is a simple string test.')

  def testLoadFileToStringWithExcessivelyLongFile(self):
    logging.error('File %s is bigger than %d bytes.',
                  self.simple_string_file, 10)
    self.mox.ReplayAll()

    result = utils.LoadFileToString(self.simple_string_file, 10)
    self.assertIsNone(result)
    self.mox.VerifyAll()

  def testLoadFileWithNonexistentFile(self):
    bad_file_name = os.path.join(self.base_dir, 'no_file_by_this_name')
    logging.error('Unable to read file %s to string: %s', bad_file_name,
                  mox.IgnoreArg())
    self.mox.ReplayAll()

    result = utils.LoadFileToString(bad_file_name)
    self.assertIsNone(result)
    self.mox.VerifyAll()

  def testParseFileToProtobufWithGoodAnalysisFile(self):
    expected_descriptor = wheelbarrow_pb2.AnalysisDescriptor()
    expected_descriptor.name = 'check_permissions'
    expected_descriptor.description = ('Check which permissions are changed by '
                                       'the package.')
    expected_descriptor.module = ('analyzers.permission_checker'
                                  '.PermissionChecker')
    expected_descriptor.category = 'file_system'
    arg = expected_descriptor.arguments.add()
    arg.string_args.append('/bin')
    arg = expected_descriptor.arguments.add()
    arg.string_args.append('/sbin')
    diff_pair = expected_descriptor.diff_pairs.add()
    diff_pair.before = wheelbarrow_pb2.EXTRACT
    diff_pair.after = wheelbarrow_pb2.INSTALL
    diff_pair = expected_descriptor.diff_pairs.add()
    diff_pair.before = wheelbarrow_pb2.EXTRACT
    diff_pair.after = wheelbarrow_pb2.REMOVE
    descriptor = wheelbarrow_pb2.AnalysisDescriptor()
    result = utils.ParseFileToProtobuf(self.good_analysis_file, descriptor, -1,
                                       True)
    self.assertTrue(result)
    str1 = text_format.MessageToString(expected_descriptor, as_one_line=True)
    str2 = text_format.MessageToString(descriptor, as_one_line=True)
    self.assertEqual(str1, str2)

  def testParseFileToProtobufWithFileLoadingFailure(self):
    protobuf = wheelbarrow_pb2.AnalysisDescriptor
    self.mox.StubOutWithMock(utils, 'LoadFileToString')
    utils.LoadFileToString(self.good_analysis_file, -1).AndReturn(None)
    logging.error('Unable to read file %s while trying to parse it as protobuf '
                  'message %s.', self.good_analysis_file, type(protobuf))
    self.mox.ReplayAll()

    result = utils.ParseFileToProtobuf(self.good_analysis_file, protobuf)
    self.assertFalse(result)
    self.mox.VerifyAll()

  def testParseFileToProtobufWithBadFieldName(self):
    bad_analysis_file = os.path.join(self.base_dir, 'analysis_bad')
    logging.error('Error while parsing file %s to protobuf message %s: %s',
                  bad_analysis_file, type(wheelbarrow_pb2.AnalysisDescriptor()),
                  mox.IgnoreArg())
    self.mox.ReplayAll()

    descriptor = wheelbarrow_pb2.AnalysisDescriptor()
    result = utils.ParseFileToProtobuf(bad_analysis_file, descriptor, -1, True)
    self.assertFalse(result)
    self.mox.VerifyAll()

  def testParseFileToProtobufWithBinaryFile(self):
    binary_file_name = os.path.join(self.base_dir,
                                    'binary_package_descriptor.dat')
    expected_descriptor = wheelbarrow_pb2.Package()
    expected_descriptor.name = 'emacspeak-ss'
    expected_descriptor.version = '1.12.1-1'
    expected_descriptor.architecture = 'i386'
    expected_descriptor.status = wheelbarrow_pb2.Package.PROCESSING
    expected_descriptor.analysis_attempts = 1

    descriptor = wheelbarrow_pb2.Package()
    result = utils.ParseFileToProtobuf(binary_file_name, descriptor)
    self.assertTrue(result)
    str1 = text_format.MessageToString(expected_descriptor, as_one_line=True)
    str2 = text_format.MessageToString(descriptor, as_one_line=True)
    self.assertEqual(str1, str2)

  def testWriteProtobufToFileWithNoExtension(self):
    package = self._CreateTestPackageProtobuf()
    path = os.path.join(self.tmp_dir, 'test_path')
    result = utils.WriteProtobufToFile(package, path, add_extension=True)
    extended_path = '%s%s' % (path, '.txt')
    CheckResultProtobufFromFile(self, package, extended_path,
                                wheelbarrow_pb2.Package())
    self.assertTrue(result)

  def testWriteProtobufToFileWithEncodeError(self):
    self.mox.StubOutWithMock(text_format, 'MessageToString')
    protobuf = self._CreateTestPackageProtobuf()
    text_format.MessageToString(protobuf).AndRaise(EncodeError)
    path = 'path_test'
    logging.error('Could not encode protobuf when writing to file %s: %s',
                  'path_test', mox.IgnoreArg())
    self.mox.ReplayAll()

    result = utils.WriteProtobufToFile(protobuf, path, True, False)
    self.assertFalse(result)
    self.mox.VerifyAll()

  def testWriteProtobufToFileWithBadFilePath(self):
    protobuf = self._CreateTestPackageProtobuf()
    path = os.path.join(self.tmp_dir, 'nonexistent_dir', 'path_test')
    logging.error('Could not write protobuf to file %s: %s', path,
                  mox.IgnoreArg())
    self.mox.ReplayAll()

    result = utils.WriteProtobufToFile(protobuf, path, False, False)
    self.assertFalse(result)
    self.mox.ReplayAll()

  def _CreateTestPackageProtobuf(self):
    package = wheelbarrow_pb2.Package()
    package.name = 'test'
    package.version = 'version_test'
    package.architecture = 'amd64'
    package.section = 'section_test'
    package.status = wheelbarrow_pb2.Package.DONE
    package.analysis_attempts = 1
    return package

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()


if __name__ == '__main__':
  unittest.main()
