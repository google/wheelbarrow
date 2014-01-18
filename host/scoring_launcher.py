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
"""Score analysis results.

     Usage: %s
       --resultdir <directory containing result protobufs>
       --scoredir <output directory>
"""

import gflags
import logging
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)
from host.scoring.result_directory_scorer import ScoreResultDirectory

FLAGS = gflags.FLAGS

gflags.DEFINE_string('resultdir', None, 'The input directory containing the '
                     'results.')
gflags.DEFINE_string('scoredir', None, 'The output directory.')
gflags.MarkFlagAsRequired('resultdir')
gflags.MarkFlagAsRequired('scoredir')


def main(argv):
  """Score analysis results."""
  logging.root.setLevel(logging.INFO)
  argv = FLAGS(argv)
  logging.info('Scoring result in %s...', FLAGS.resultdir)
  ScoreResultDirectory(FLAGS.resultdir, FLAGS.scoredir)


if __name__ == '__main__':
  main(sys.argv)
