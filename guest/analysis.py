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
"""A single analysis.

The Analysis class wraps an analysis descriptor and the corresponding analysis
module (Analyzer).
"""

import os.path
import logging
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from guest.argument_preprocessor import PreprocessArgument
from guest.triggers import TriggerManager


class Error(Exception):
  pass


class RecoverableAnalysisError(Error):
  """A benign analysis error.

  This kind of error should be caught at the Analysis level and allow the
  process to carry on.
  """
  pass


class FatalAnalysisError(Error):
  """A serious analysis error.

  This kind of error should be caught at the outermost level (broker) and
  require terminating the analysis process and marking it as failed in the
  result protobuf.
  """
  pass


class Analysis(object):
  """A class that represents an analysis.

  Attributes:
    _descriptor: The descriptor for this analysis.
    _triggers: A list of triggers after which this analysis should be run.
    _module: The module to be executed after each trigger.
  """

  def __init__(self, descriptor, triggers, module):
    self._descriptor = descriptor
    self._triggers = triggers
    self._module = module

  def RunAnalysis(self, trigger):
    """Run the analysis after a given trigger if appropriate.

    Args:
      trigger: The latest trigger performed by the broker.
    """

    if trigger in self._triggers:
      logging.info('Running analysis %s for trigger %d', self._descriptor.name,
                   trigger)
      for argument in self._descriptor.arguments:
        try:
          argument = PreprocessArgument(argument,
                                        TriggerManager.GetPackageExtractDir())
          self._module.RunAnalysis(trigger, argument, self._descriptor.suite)
        except RecoverableAnalysisError as e:
          logging.error('Analysis error while running %s: %s',
                        self._descriptor.name, e)

  def AddResults(self, application_result):
    """Add individual results to an ApplicationResult object.

    This function adds all results for all descriptive and diff analyses. Due to
    the fact that protobufs do not support assignment of fields without doing a
    deep copy, we systematically create a new analysis result. The newly created
    analysis result may not get populated, if an analysis does not have any
    results. That is why we delete any empty analysis results.

    Args:
      application_result: The ApplicationResult object for the application
                          under test.
    """

    analysis_result = application_result.analysis_results.add()
    analysis_result.analysis_name = self._descriptor.name

    for trigger in self._descriptor.descriptive_triggers:
      self._module.AddDescriptiveResults(trigger, analysis_result)
    for diff_pair in self._descriptor.diff_pairs:
      self._module.AddDiffResults(diff_pair, analysis_result)

    if not analysis_result.results:
      del application_result.analysis_results[-1]
