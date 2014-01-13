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
"""A manager for suite file results."""

import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


class FileResultSuiteManager(object):
  """A class to manage suite results for file analyses."""

  _suite_results = {}

  @staticmethod
  def SuiteExists(suite_name):
    """Determine if a suite exists, given its name."""

    return FileResultSuiteManager._suite_results.get(suite_name) is not None

  @staticmethod
  def GetSuiteResult(suite_name, trigger_or_diff_pair, path):
    """Get a suite result.

    Args:
      suite_name: A suite name.
      trigger_or_diff_pair: A trigger or a diff pair.
      path: A file path.

    Returns:
      A result if it was found, None otherwise.
    """

    try:
      return FileResultSuiteManager._suite_results[suite_name][
          str(trigger_or_diff_pair)][path]
    except KeyError:
      return None

  @staticmethod
  def AddFileResult(suite_name, trigger_or_diff_pair, path, result):
    """Add a file result to an analysis suite.

    Args:
      suite_name: The name of a suite.
      trigger_or_diff_pair: A trigger or a diff pair.
      path: A file path.
      result: An analysis result.
    """

    # Get the suite file result or create one.
    suite_result = None
    if suite_name in FileResultSuiteManager._suite_results:
      suite_result = FileResultSuiteManager._suite_results[suite_name]
    else:
      suite_result = {}
      FileResultSuiteManager._suite_results[suite_name] = suite_result
    trigger_or_diff_pair_str = str(trigger_or_diff_pair)
    if trigger_or_diff_pair_str not in suite_result:
      suite_result[trigger_or_diff_pair_str] = {}
    suite_result[trigger_or_diff_pair_str][path] = result
