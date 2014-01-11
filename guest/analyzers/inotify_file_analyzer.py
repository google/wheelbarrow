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
"""Inotify file analyzer."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2
from guest.analyzers.file_analyzer import FileAnalyzer
from guest.analyzers.inotify_manager import InotifyManager


class InotifyFileAnalyzer(FileAnalyzer):
  """Performs detection of events affecting files using inotify.

  Subclasses should implement the _GetEventNames() method, which returns a list
  of inotify events that are being watched.
  """

  def __init__(self):
    self._inotify_manager = InotifyManager()
    self._watched_paths = set()
    super(InotifyFileAnalyzer, self).__init__()

  def _GetEventNames(self):
    """Get the names of the inotify events that are being watched.

    This method should be implemented by subclasses. It should return a list of
    inotify events that are being watched (list of strings).
    """

    raise NotImplementedError

  def RunAnalysis(self, trigger, argument, unused_suite):
    """Perform an inotify file analysis.

    When the path argument is a directory, we may get results for several files,
    so we cannot just follow the model of FileAnalyzer (one result per path).
    That is why we need to override RunAnalysis. The first time this is called
    on a path, we start watching it. At each trigger, we record a counter
    mapping affected paths to the number of times it was affected by events.

    We only take one snapshot per trigger for all paths A single snapshot has
    the information for all paths that are already being tracked. Even if we
    start tracking a new path, the count of events for the new path should be
    0. If it is not, it means that something is interacting with the path
    between two triggers and we may be missing some events on that path anyway.
    So for now we just assume that the initial event count is 0.

    Args:
      trigger: A trigger.
      argument: A list of pairs (absolute path, relative path) for the paths
                should be watched.
    """

    event_names = self._GetEventNames()
    for (_, rel_path) in argument:
      if rel_path not in self._watched_paths:
        self._watched_paths.add(rel_path)
        self._inotify_manager.StartWatchingPath(rel_path, event_names)
    if trigger in self._analysis_results:
      return
    snapshot = self._inotify_manager.GetAffectedPaths(event_names)
    self._analysis_results[trigger] = snapshot
    for path in snapshot.elements():
      self._RecordFileType(path, path)

  def AddDiffResults(self, diff_pair, analysis_result):
    before = self._GetAnalysisResultForTrigger(diff_pair.before)
    after = self._GetAnalysisResultForTrigger(diff_pair.after)

    affected_files = after - before
    for path in affected_files:
      self._PrepareDiffFileResult(path, analysis_result, wheelbarrow_pb2.ADD,
                                  diff_pair)
      # We don't record anything. We just want to know that some event happened
      # to a file.


class InotifyFileReadModifyMoveAnalyzer(InotifyFileAnalyzer):
  """Performs detection of file reads, writes and moves using inotify."""

  def _GetEventNames(self):
    return ['IN_ACCESS', 'IN_ATTRIB', 'IN_DELETE', 'IN_DELETE_SELF',
            'IN_MODIFY', 'IN_MOVED_FROM', 'IN_MOVED_FROM', 'IN_MOVED_TO']
