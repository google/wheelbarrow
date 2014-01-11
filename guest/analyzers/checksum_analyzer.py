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
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from common.utils import LoadFileToString
from guest.analysis import RecoverableAnalysisError
from guest.analyzers.file_analyzer import FileAnalyzer


class ChecksumAnalyzer(FileAnalyzer):
  """An analyzer that computes file hashes."""

  def _PerformAnalysis(self, file_path):
    """Perform a checksum analysis on a file.

    Args:
      file_path: The path to a file.

    Returns:
      A tuple with the MD5, SHA-1 and SHA-256 hashes of the input file.
    """

    contents = LoadFileToString(file_path)
    if not contents:
      raise RecoverableAnalysisError('Could not load file %s for hashing.'
                                     % file_path)
    md5hash = FileAnalyzer._ComputeStringHash(contents, hashlib.md5)
    sha1hash = FileAnalyzer._ComputeStringHash(contents, hashlib.sha1)
    sha256hash = FileAnalyzer._ComputeStringHash(contents, hashlib.sha256)
    return (md5hash, sha1hash, sha256hash)

  def AddDescriptiveResults(self, trigger, analysis_result):
    descriptive_result = self._GetAnalysisResultForTrigger(trigger)
    for (path, hashes) in descriptive_result.iteritems():
      res = self._PrepareDescriptiveFileResult(path, analysis_result, trigger)
      res.states[0].md5 = hashes[0]
      res.states[0].sha1 = hashes[1]
      res.states[0].sha256 = hashes[2]
