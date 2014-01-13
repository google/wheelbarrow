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
"""Inotify manager test."""

import os
import sys
import shutil
import tempfile
import unittest
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from guest.analyzers import inotify_manager


TEST_PATH = 'guest/analyzers_test/test_data'
TMP_PATH = tempfile.gettempdir()


class InotifyManagerTest(unittest.TestCase):
  def setUp(self):
    self.base_dir = os.path.join(WHEELBARROW_HOME, TEST_PATH)
    self.test_file_name = 'permission_analyzer_diff_results'
    self.test_path = os.path.join(self.base_dir, self.test_file_name)
    self.tmp_dir = os.path.join(TMP_PATH, 'inotify_manager')
    shutil.rmtree(self.tmp_dir, ignore_errors=True)
    os.mkdir(self.tmp_dir)
    inotify_manager.InotifyManager._process_event = None
    inotify_manager.InotifyManager._watch_manager = None
    inotify_manager.InotifyManager._notifier = None

  def testMakeMaskFromEventNames(self):
    events = ['IN_ACCESS', 'IN_DELETE']
    expected_mask = 0x201
    mask = inotify_manager.InotifyManager._MakeMaskFromEventNames(events)
    self.assertEqual(mask, expected_mask)

  def testStartWatchingPathWithFile(self):
    manager = inotify_manager.InotifyManager()
    manager.StartWatchingPath(self.test_path, ['IN_ACCESS', 'IN_DELETE'])
    InotifyManagerTest._GenerateOpenAndAccessEvents(self.test_path)
    affected_paths = manager.GetAffectedPaths(['IN_ACCESS'])
    self._CheckCounterResult(affected_paths, self.test_path, 1)

  def testGetAffectedPathsWithNonOccurringEvent(self):
    manager = inotify_manager.InotifyManager()
    manager.StartWatchingPath(self.test_path, ['IN_ACCESS', 'IN_DELETE'])
    InotifyManagerTest._GenerateOpenAndAccessEvents(self.test_path)
    affected_paths = manager.GetAffectedPaths(['IN_ACCESS', 'IN_DELETE'])
    self._CheckCounterResult(affected_paths, self.test_path, 1)

  def testStartWatchingPathWithSubdirectory(self):
    test_subdir = os.path.join(self.tmp_dir, 'test_subdir')
    os.mkdir(test_subdir)
    test_path = os.path.join(test_subdir, self.test_file_name)
    shutil.copyfile(self.test_path, test_path)
    manager = inotify_manager.InotifyManager()
    manager.StartWatchingPath(self.tmp_dir, ['IN_ACCESS', 'IN_OPEN'])
    InotifyManagerTest._GenerateOpenAndAccessEvents(test_path)
    affected_paths = manager.GetAffectedPaths(['IN_ACCESS', 'IN_OPEN'])
    self._CheckCounterResult(affected_paths, test_path, 2)

  def _CheckCounterResult(self, counter, key, count):
    self.assertIn(key, counter)
    self.assertEqual(counter[key], count)

  @staticmethod
  def _GenerateOpenAndAccessEvents(file_path):
    test_file = open(file_path)
    test_file.read()
    test_file.close()


if __name__ == '__main__':
  unittest.main()
