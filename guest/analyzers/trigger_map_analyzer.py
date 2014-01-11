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
"""An Analyzer abstract class with a trigger map."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from collections import namedtuple
from guest.analysis import RecoverableAnalysisError
from guest.analyzers.analyzer import Analyzer


class TriggerMapAnalyzer(Analyzer):
  """An Analyzer abstract class with a trigger map.

  This class has some utility methods to process results from analyses after
  running several different triggers. These are kept out of the Analyzer class
  itself to keep the Analyzer interface clean.
  """

  def __init__(self):
    self._analysis_results = {}

  def _AddAnalysisResult(self, trigger, result):
    """Add an analysis result.

    Args:
      trigger: The trigger associated with the result.
      result: An analysis result to add.
    """

    existing_results = self._analysis_results.get(trigger, {})
    self._analysis_results[trigger] = dict(existing_results.items()
                                           + result.items())

  def _GetAnalysisResultForTrigger(self, trigger):
    """Get an analysis result, given a trigger.

    Args:
      trigger: A trigger.

    Returns:
      The analysis result for the given trigger.

    Raises:
      RecoverableAnalysisError if there are no results for the trigger.
    """

    try:
      return self._analysis_results[trigger]
    except KeyError:
      raise RecoverableAnalysisError

  def _GetDetailedAnalysisResultForDiffPair(self, diff_pair):
    """Get a detailed analysis result for a diff pair.

    For a given diff pair, this function computes the set of common keys (e.g.,
    file paths), the set of added keys and the set of removed keys.

    Args:
      diff_pair: A diff pair.

    Returns:
      A named tuple of the form (map before, map after, common key, added_keys,
      removed key).
    """

    diff_result = namedtuple(
        'diff_result', 'before, after, common_keys, added_keys, removed_keys')
    try:
      before = self._GetAnalysisResultForTrigger(diff_pair.before)
      before_keys = set(before.keys())
      after = self._GetAnalysisResultForTrigger(diff_pair.after)
      after_keys = set(after.keys())
    except RecoverableAnalysisError:
      return diff_result({}, {}, set(), set(), set())
    common_keys = before_keys & after_keys
    removed_keys = before_keys - common_keys
    added_keys = after_keys - common_keys

    return diff_result(before, after, common_keys, added_keys, removed_keys)
