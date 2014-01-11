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
"""Checksum analyzer."""

import hashlib
import logging
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2
from common.utils import LoadFileToString
from guest.analysis import RecoverableAnalysisError
from guest.analyzers.file_analyzer import FileAnalyzer


class ChecksumFileWriteAnalyzer(FileAnalyzer):
  """An analyzer for file contents.

  This analyzer checks for modifications in a file by comparing file checksums.
  It can also record the file contents if instantiated with the record_contents
  argument set to True.
  """

  def __init__(self, record_contents):
    """Constructor.

    Args:
      record_contents: True if the analyzer should record the contents of the
                       files it analyzes.
    """

    super(ChecksumFileWriteAnalyzer, self).__init__()
    self._record_contents = record_contents

  def _PerformAnalysis(self, file_path):
    contents = LoadFileToString(file_path)
    if not contents:
      raise RecoverableAnalysisError('Could not load file %s for hashing.'
                                     % file_path)
    checksum = FileAnalyzer._ComputeStringHash(contents, hashlib.sha256)
    return (checksum, contents) if self._record_contents else (checksum, None)

  def AddDescriptiveResults(self, trigger, analysis_result):
    # A descriptive result does not make sense if the contents are not recorded.
    if not self._record_contents:
      logging.warning('Descriptive results requested for FileContentsAnalyzer '
                      'without recording contents.')
    descriptive_result = self._GetAnalysisResultForTrigger(trigger)
    for (path, result) in descriptive_result.iteritems():
      res = self._PrepareDescriptiveFileResult(path, analysis_result, trigger)
      if self._record_contents:
        res.states[0].contents = result[1]

  def AddDiffResults(self, diff_pair, analysis_result):
    """Get the diff result of this analysis."""

    diff_result = self._GetDetailedAnalysisResultForDiffPair(diff_pair)

    for key in diff_result.added_keys:
      result = self._PrepareDiffFileResult(key, analysis_result,
                                           wheelbarrow_pb2.ADD, diff_pair)
      result.states[1].sha256 = diff_result.after[key][0]
      if self._record_contents:
        result.states[1].contents = diff_result.after[key][1]

    for key in diff_result.removed_keys:
      result = self._PrepareDiffFileResult(key, analysis_result,
                                           wheelbarrow_pb2.DELETE, diff_pair)
      result.states[0].sha256 = diff_result.after[key][0]
      if self._record_contents:
        result.states[0].contents = diff_result.before[key][1]

    for key in diff_result.common_keys:
      if diff_result.before[key][0] != diff_result.after[key][0]:
        result = self._PrepareDiffFileResult(key, analysis_result,
                                             wheelbarrow_pb2.CHANGE, diff_pair)
        result.states[0].contents = diff_result.before[key][0]
        result.states[1].contents = diff_result.after[key][0]
        if self._record_contents:
          result.states[0].contents = diff_result.before[key][1]
          result.states[1].contents = diff_result.after[key][1]


class RecordingChecksumFileWriteAnalyzer(ChecksumFileWriteAnalyzer):
  def __init__(self):
    super(RecordingChecksumFileWriteAnalyzer, self).__init__(True)


class NonRecordingChecksumFileWriteAnalyzer(ChecksumFileWriteAnalyzer):
  def __init__(self):
    super(NonRecordingChecksumFileWriteAnalyzer, self).__init__(False)
