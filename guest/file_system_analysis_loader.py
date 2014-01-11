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
"""A loader for analyses with descriptors on a file system."""

import os.path
import logging
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

import glob


from common.utils import ParseFileToProtobuf
from common.wheelbarrow_pb2 import AnalysisDescriptor
from guest.analysis import Analysis
from guest.analysis_loader import AnalysisLoader
from guest.analysis_loader import AnalysisLoadingError
from guest.analyzers.analyzer import Analyzer


class FileSystemAnalysisLoader(AnalysisLoader):
  """Loader for analyses on a file system."""

  # Limit for file read, chosen to be much bigger than any analysis descriptor
  # we expect.
  _FILE_SIZE_LIMIT = 1024 * 1024

  def __init__(self, srcs):
    """Constructor for the file system analysis loader.

    Args:
      srcs: The list of analysis descriptor file names (as globbable strings).
    """

    self._srcs = srcs

  def LoadAnalyses(self):
    """Load analyses from a file system.

    The file names for the analysis descriptors should be set when the class is
    instantiated.

    Returns:
      A list of analyses parsed from a file system.

    Raises:
      AnalysisLoadingError if the input files cannot be globbed.
    """

    analyses = []
    for src in self._srcs:
      descriptor_file_names = None
      descriptor_file_names = glob.glob(src)
      if not descriptor_file_names:
        logging.error('Unable to get descriptor file names by globbing %s', src)
        raise AnalysisLoadingError('Unable to get descriptor file names by '
                                   'globbing %s')
      for descriptor_file_name in descriptor_file_names:
        if os.path.isdir(descriptor_file_name):
          continue
        descriptor = FileSystemAnalysisLoader._ParseAnalysisDescriptor(
            descriptor_file_name)
        if descriptor is None:
          logging.error('Failed to parse descriptor from file %s',
                        descriptor_file_name)
          continue
        triggers = AnalysisLoader._GetTriggersFromDescriptor(descriptor)
        analyzer = None
        try:
          analyzer = AnalysisLoader._GetInstanceByClassName(descriptor.module)
        except AnalysisLoadingError as e:
          logging.error('Could not instantiate %s: %s', descriptor.module, e)
          continue
        if not isinstance(analyzer, Analyzer):
          logging.error('%s is not an Analyzer in analysis %s',
                        descriptor.module, descriptor_file_name)
          continue
        analyses.append(Analysis(descriptor, triggers, analyzer))
    return analyses

  @staticmethod
  def _ParseAnalysisDescriptor(file_name, file_size_limit=_FILE_SIZE_LIMIT):
    """Parse an analysis descriptor.

    Args:
      file_name: Path to the file containing a text version of the descriptor.
      file_size_limit: The maximum number of bytes to be read from the file.

    Returns:
      The analysis descriptor if all goes well, None otherwise.
    """

    analysis_descriptor = AnalysisDescriptor()

    if ParseFileToProtobuf(file_name, analysis_descriptor, file_size_limit,
                           True):
      return analysis_descriptor
    else:
      return None
