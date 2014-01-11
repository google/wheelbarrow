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
"""Result directory scorer."""

import glob
import logging
import os.path
import sys

WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)
from common.utils import WriteProtobufToFile
from host.scoring import application_scorer


def ScoreResultDirectory(input_dir, output_dir, text_out=True):
  """Result directory scorer."""
  file_paths = glob.glob(os.path.join(input_dir, '*'))
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  scorer = application_scorer.ApplicationScorer()
  for file_path in file_paths:
    try:
      score = scorer.Score(file_path)
      file_name = os.path.basename(file_path)
      score_file_path = os.path.join(output_dir, file_name)
      if not WriteProtobufToFile(score, score_file_path, text_out, False):
        logging.error('Could not write score to file %s.', score_file_path)
    except application_scorer.Error as err:
      logging.error('Could not score package file %s: %s', file_path, err)
