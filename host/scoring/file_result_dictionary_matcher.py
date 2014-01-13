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
"""Scoring lookups."""

import sys
import os.path
import re
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from common.wheelbarrow_pb2 import ResultScore


class FileResultDictionaryMatcher(object):
  """Dictionary score lookup."""
  def __init__(self, score_dictionary_entry):
    self._entry = score_dictionary_entry
    self._compiled_path = (re.compile(score_dictionary_entry.path)
                           if score_dictionary_entry.path else None)

  def Match(self, result):
    """Match a file result with this matcher.

    At the moment, we only consider the file path and the result type. This
    allows us to score some important result types (e.g., removing or changing
    an important file). This can be extended to take into account the file
    states as well. Note that, if we come to that function, we already know that
    the analysis name matches as well.

    Args:
      result: A file result.

    Returns:
      A wheelbarrow_pb.ResultScore if a match was found, None otherwise.
    """

    if self._compiled_path and not self._compiled_path.match(result.path):
      return None

    if (self._entry.result_type
        and self._entry.result_type != result.type):
      return None

    result_score = ResultScore()
    result_score.result_name = (self._entry.result_name
                                if self._entry.result_name
                                else self._entry.analysis_name)
    result_score.score = self._entry.score
    return result_score
