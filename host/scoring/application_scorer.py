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
"""Score analysis results."""

from collections import Counter
import glob
import logging
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from common import wheelbarrow_pb2
from common.utils import ParseFileToProtobuf
from host.scoring.file_result_scorer import FileResultScorer


class Error(Exception):
  pass


class FatalScorerError(Error):
  pass


class NoResultError(Error):
  pass


class ApplicationScorer(object):
  """An application scorer."""

  _FILE_SYSTEM_DICTIONARY = 'file_system_score_dictionary'
  _PACKAGE_DICTIONARY = 'package_score_dictionary'

  def __init__(self):
    root_dir = WHEELBARROW_HOME
    dictionary_base_dir = os.path.join(
        root_dir, 'host/scoring')
    fs_path = os.path.join(
        dictionary_base_dir, ApplicationScorer._FILE_SYSTEM_DICTIONARY, '*')
    self._file_system_result_scorer = FileResultScorer(glob.glob(fs_path))
    package_path = os.path.join(
        dictionary_base_dir, ApplicationScorer._PACKAGE_DICTIONARY, '*')
    self._package_result_scorer = FileResultScorer(glob.glob(package_path))

  def Score(self, file_path):
    """Score an application.

    Args:
      file_path: The path to a file containing a
      wheelbarrow_pb2.ApplicationResult.

    Returns:
      A wheelbarrow_pb2.DetailedPackageScore.

    Raises:
      FatalScorerError: If the result file cannot be parsed.
      NoResultError: If the application has not been successfully analyzed.
    """

    application_result = wheelbarrow_pb2.ApplicationResult()
    if not ParseFileToProtobuf(file_path, application_result):
      error = 'Could not parse application result from file %s.' % file_path
      logging.error(error)
      raise FatalScorerError(error)

    status = application_result.package.status
    if status != wheelbarrow_pb2.Package.DONE:
      raise NoResultError('No result found in file %s: package status %d.' %
                          (file_path, status))

    # Map file to score.
    package_level_file_score_map = dict()

    # Map analysis name to score.
    self._analysis_scores = Counter()

    for analysis_result in application_result.analysis_results:
      analysis_name = analysis_result.analysis_name
      for result in analysis_result.results:
        for package_result in result.package_results:
          score = self._package_result_scorer.Score(analysis_name,
                                                    package_result)
          if score:
            self._AddSingleScore(package_level_file_score_map, analysis_name,
                                 package_result.path, score)
        for file_system_result in result.file_system_results:
          score = self._file_system_result_scorer.Score(analysis_name,
                                                        file_system_result)
          if score:
            self._AddSingleScore(package_level_file_score_map, analysis_name,
                                 file_system_result.path, score)

    # Populate the final score protobuf.
    detailed_package_score = wheelbarrow_pb2.DetailedPackageScore()
    detailed_package_score.package.CopyFrom(application_result.package)
    detailed_package_score.file_result_scores.extend(
        package_level_file_score_map.values())
    for (key, value) in self._analysis_scores.items():
      analysis_score = detailed_package_score.overall_result_scores.add()
      analysis_score.result_name = key
      analysis_score.score = value
    detailed_package_score.package_score = sum(self._analysis_scores.values())

    return detailed_package_score

  def _AddSingleScore(self, score_map, analysis_name, file_id, score):
    """Add a single analysis score for a single file.

    Args:
      score_map: A dict mapping file name to the corresponding
                 wheelbarrow_pb2.
      analysis_name: An analysis name.
      file_id: An identifier for the file (usually the file path).
      score: A wheelbarrow_pb2.ResultScore.
    """

    package_level_file_score = None
    if file_id in score_map:
      package_level_file_score = score_map[file_id]
    else:
      package_level_file_score = wheelbarrow_pb2.PackageLevelFileScore()
      package_level_file_score.path = file_id
      score_map[file_id] = package_level_file_score
    new_score = package_level_file_score.result_scores.add()
    new_score.CopyFrom(score)
    # Increment the package-level score (one per file).
    package_level_file_score.overall_score += score.score

    # Increment the file-level score (one per analysis).
    self._analysis_scores[analysis_name] += score.score
