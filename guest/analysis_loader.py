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
"""Base class and exception for analysis loading.

This class contains a LoadAnalyses method that all analysis loaders should
implement. It also contains some utility methods to be used during analysis
loading.
"""

import logging
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


class Error(Exception):
  pass


class AnalysisLoadingError(Error):
  pass


class AnalysisLoader(object):
  """Base class for an analysis loader."""

  def LoadAnalyses(self):
    raise NotImplementedError

  @staticmethod
  def _GetTriggersFromDescriptor(descriptor):
    """Get the triggers contained in an AnalysisDescriptor.

    Args:
      descriptor: An AnalysisDescriptor.

    Returns:
      The set of triggers contained in the input descriptor.
    """

    triggers = set()
    for trigger in descriptor.descriptive_triggers:
      triggers.add(trigger)
    for diff_pair in descriptor.diff_pairs:
      triggers.add(diff_pair.before)
      triggers.add(diff_pair.after)
    return triggers

  @staticmethod
  def _GetInstanceByClassName(class_name):
    """Get a new instance by its class name.

    Args:
      class_name: The name of the class to instantiate.

    Returns:
      An instance of the requested class.

    Raises:
      AnalysisLoadingError if there is an issue instantiating the class.
    """

    parts = class_name.split('.')
    module = '.'.join(parts[:-1])
    try:
      m = __import__(module)
      for part in parts[1:]:
        m = getattr(m, part)
      return m()
    except (AttributeError, ImportError, TypeError, ValueError) as err:
      logging.error('Could not instantiate class %s: %s', class_name, err)
      raise AnalysisLoadingError('Could not instantiate class %s' % class_name)
