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
"""Tests for AnalysisLoader class."""

import email
import logging
import mox
import os.path
import sys
import unittest
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2
import guest.analysis_loader as loader


class AnalysisLoaderTest(unittest.TestCase):
  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(logging, 'error')

  def testLoadAnalyses(self):
    analysis_loader = loader.AnalysisLoader()
    self.assertRaises(NotImplementedError, analysis_loader.LoadAnalyses)

  def testGetTriggersFromDescriptor(self):
    descriptor = wheelbarrow_pb2.AnalysisDescriptor()
    descriptor.descriptive_triggers.append(wheelbarrow_pb2.INSTALL)
    descriptor.descriptive_triggers.append(wheelbarrow_pb2.RUN_BINARIES)
    diff_pair = descriptor.diff_pairs.add()
    diff_pair.before = wheelbarrow_pb2.EXTRACT
    diff_pair.after = wheelbarrow_pb2.INSTALL
    diff_pair = descriptor.diff_pairs.add()
    diff_pair.before = wheelbarrow_pb2.EXTRACT
    diff_pair.after = wheelbarrow_pb2.REMOVE
    triggers = loader.AnalysisLoader._GetTriggersFromDescriptor(descriptor)
    self.assertEqual(triggers, set([wheelbarrow_pb2.EXTRACT,
                                    wheelbarrow_pb2.INSTALL,
                                    wheelbarrow_pb2.RUN_BINARIES,
                                    wheelbarrow_pb2.REMOVE]))

  def testGetInstanceByClassNameWithGoodClassName(self):
    # Class with a no-argument constructor.
    class_name = 'email.parser.FeedParser'
    instance = loader.AnalysisLoader._GetInstanceByClassName(class_name)
    self.assertIsInstance(instance, email.parser.FeedParser)

  def testGetInstanceByClassNameWithBadClassName(self):
    class_name = 'email.parser.FeedParse'
    self._PerformBadInstantiation(class_name)

  def testGetInstanceByClassNameWithBadConstructor(self):
    # Class without a no-argument constructor.
    class_name = 'email.generator.Generator'
    self._PerformBadInstantiation(class_name)

  def _PerformBadInstantiation(self, class_name):
    logging.error('Could not instantiate class %s: %s', class_name,
                  mox.IgnoreArg())
    self.mox.ReplayAll()
    self.assertRaises(loader.AnalysisLoadingError,
                      loader.AnalysisLoader._GetInstanceByClassName, class_name)
    self.mox.VerifyAll()

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.ResetAll()


if __name__ == '__main__':
  unittest.main()
