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
"""Check file permissions for changes."""

import os
import stat
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from common import wheelbarrow_pb2
from guest.analyzers.file_analyzer import FileAnalyzer


class PermissionAnalyzer(FileAnalyzer):
  """Performs file permission analyses."""

  def _PerformAnalysis(self, file_path):
    """Perform a permission analysis.

    Determine the permission of a file given as an argument and return the octal
    permission representation as a string.

    Args:
      file_path: The path to a file.

    Returns:
      A permission string  (octal representation).
    """

    return oct(os.stat(file_path)[stat.ST_MODE])[-4:]

  def AddDescriptiveResults(self, descriptive_trigger, analysis_result):
    """Get the descriptive results of this analysis."""

    descriptive_results = self._GetAnalysisResultForTrigger(descriptive_trigger)
    for (path, permissions) in descriptive_results.iteritems():
      res = self._PrepareDescriptiveFileResult(path, analysis_result,
                                               descriptive_trigger)
      res.states[0].permissions = permissions

  def AddDiffResults(self, diff_pair, analysis_result):
    """Get the diff results of this analysis."""

    diff_result = self._GetDetailedAnalysisResultForDiffPair(diff_pair)

    for key in diff_result.added_keys:
      result = self._PrepareDiffFileResult(key, analysis_result,
                                           wheelbarrow_pb2.ADD, diff_pair)
      result.states[1].permissions = diff_result.after[key]

    for key in diff_result.removed_keys:
      result = self._PrepareDiffFileResult(key, analysis_result,
                                           wheelbarrow_pb2.DELETE, diff_pair)
      result.states[0].permissions = diff_result.before[key]

    for key in diff_result.common_keys:
      if diff_result.before[key] != diff_result.after[key]:
        result = self._PrepareDiffFileResult(key, analysis_result,
                                             wheelbarrow_pb2.CHANGE, diff_pair)
        result.states[0].permissions = diff_result.before[key]
        result.states[1].permissions = diff_result.after[key]
