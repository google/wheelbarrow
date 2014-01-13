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
"""This is the base class that all analyzers should subclass."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


class Analyzer(object):
  """Base class that all analyzers should subclass.

  An analyzer is a class which perform some analysis (e.g., check modifications
  to a file).
  """

  def RunAnalysis(self, trigger, argument, suite):
    """Run the analysis.

    Args:
      trigger: The trigger after which the analysis is being run.
      argument: An argument used by this analysis (e.g., file name).
      suite: The suite the analysis is a part of, if any.
    """

    raise NotImplementedError

  def AddDescriptiveResults(self, trigger, analysis_result):
    """Generate and add descriptive results.

    Args:
      trigger: The trigger for which the result is requested.
      analysis_result: The analysis_result to which this descriptive result is
                       being added.
    """

    raise NotImplementedError

  def AddDiffResults(self, diff_pair, analysis_result):
    """Generate and add diff results.

    Args:
      diff_pair: The diff pair for which the result is requested.
      analysis_result: The analysis_result to which this diff result is being
                       added.
    """

    raise NotImplementedError
