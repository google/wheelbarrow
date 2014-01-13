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
"""Score the results of analysis."""
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from common import wheelbarrow_pb2
from common.utils import ParseFileToProtobuf
from host.scoring.file_result_dictionary_matcher import FileResultDictionaryMatcher


class FileResultScorer(object):
  """A file result scorer."""

  def __init__(self, srcs):
    """Constructor.

    Args:
      srcs: A list of paths to files containing
            wheelbarrow_pb2.FileResultScoreDictionaryEntry protobufs.
    """

    self._InitializeScoreDictionary(srcs)

  def Score(self, analysis_name, file_result):
    """Score a file result.

    Args:
      analysis_name: The name of the analysis that generated the file result.
      file_result: A wheelbarrow_pb2.FileResult.

    Returns:
      A wheelbarrow_pb2.ResultScore if the file result has a score, None
      otherwise.
    """

    if analysis_name not in self._dictionary:
      return None

    for entry in self._dictionary[analysis_name]:
      # We only use matchers with the right analysis name, which excludes a lot
      # of irrelevant matchers.
      score = entry.Match(file_result)
      if score:
        return score

    return None

  def _InitializeScoreDictionary(self, srcs):
    """Initialize a score dictionary.

    This loads score dictionary entries for scoring file results. It
    populates the internal self._dictionary, which maps analysis names to
    dictionary matchers. This allows us to do a first matching on the analysis
    name when we try to match a file result to a score.

    Args:
      srcs: A list of paths to files containing
      wheelbarrow_pb2.FileResultScoreDictionaryEntry protobufs.
    """

    self._dictionary = {}

    for src in srcs:
      entry = wheelbarrow_pb2.FileResultScoreDictionaryEntry()
      if not ParseFileToProtobuf(src, entry, -1, True):
        logging.error('Could not parse dictionary entry file %s.', src)
        continue
      if not entry.analysis_name:
        continue
      matcher = FileResultDictionaryMatcher(entry)
      if entry.analysis_name in self._dictionary:
        self._dictionary[entry.analysis_name].append(matcher)
      else:
        self._dictionary[entry.analysis_name] = [matcher]
