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
"""This is the base class for file analyzers.

It encapsulates utilities specific to file analyses.
"""

import os.path
import logging
import subprocess
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2
from guest import analysis
from guest.analyzers.trigger_map_analyzer import TriggerMapAnalyzer
from guest.file_result_suite_manager import FileResultSuiteManager


class FileAnalyzer(TriggerMapAnalyzer):
  """Base class for file analyzers.

  Subclasses should implement _PerformAnalysis.
  """

  _NO_SUITE = ''  # Default value for strings in protobufs.
  _package_binaries = set()

  def __init__(self):
    super(FileAnalyzer, self).__init__()
    self._file_types = {}
    self._analysis_suite = FileAnalyzer._NO_SUITE

  def RunAnalysis(self, trigger, argument, suite):
    """Run a standard file analysis.

    This is a standard method for a file analysis. It performs some work
    (delegated to the subclass) and for each file, it records the analysis
    result. An important detail to note is that each analysis result is
    associated with the file's "relative" path. In particular, if we are
    analyzing the contents of an extracted package under /tmp/[blah]/[rel_path],
    it associates the result with [rel_path].

    Args:
      trigger: The trigger after which the analysis is performed.
      argument: An analyzer argument.
      suite: The suite the analysis is a part of, if any.
    """

    self._analysis_suite = suite
    analysis_result = {}
    for (file_path, rel_path) in argument:
      analysis_result[rel_path] = self._PerformAnalysis(file_path)
      self._RecordFileType(file_path, rel_path)
      if (suite == 'package'
          and self._GetFileType(rel_path) == wheelbarrow_pb2.FileResult.BINARY):
        FileAnalyzer._package_binaries.add(rel_path)
    self._AddAnalysisResult(trigger, analysis_result)

  @staticmethod
  def GetBinaries():
    """Get the list of binaries in the packages."""

    return FileAnalyzer._package_binaries

  def _PerformAnalysis(self, file_path):
    """Perform some analysis work.

    Subclasses have to implement this method.

    Args:
      file_path: The path to the file the analysis should be performed on.

    Returns:
      The analysis results for the input file.
    """

    raise NotImplementedError

  def _RecordFileType(self, file_path, file_key=None):
    """Record the type of a file.

    Args:
      file_path: The path to a file.
      file_key: The key under which the file type should be recorded.
    """

    if file_key is None:
      file_key = file_path
    if file_key not in self._file_types:
      self._file_types[file_key] = FileAnalyzer._DetermineFileType(file_path)

  def _GetFileType(self, file_key):
    """Get the previously recorded type of a file.

    Note that the file type should have previously been recorded using the
    _RecordFileType() method.

    Args:
      file_key: A file key (usually a file path).

    Returns:
      The file type.
    """

    return self._file_types[file_key]

  @staticmethod
  def _DetermineFileType(file_name):
    """Determine the type of a file.

    Args:
      file_name: The path to the file whose type has to be determined.

    Returns:
      The type of the file.

    Raises:
      RecoverableAnalysisError if something went wrong when executing file.
    """

    file_output = None
    try:
      file_output = subprocess.check_output(['/usr/bin/file', file_name])
    except (subprocess.CalledProcessError, OSError, ValueError) as e:
      logging.error('Could not execute file on %s: %s', file_name, e)
      raise analysis.RecoverableAnalysisError('Could not determine file type '
                                              'for %s', file_name)
    if 'shell script' in file_output:
      return wheelbarrow_pb2.FileResult.SCRIPT
    elif 'ELF' in file_output:
      return wheelbarrow_pb2.FileResult.BINARY
    elif 'text' in file_output:
      return wheelbarrow_pb2.FileResult.TEXT
    else:
      return wheelbarrow_pb2.FileResult.OTHER

  def _PrepareDiffFileResult(self, path, analysis_result, result_type,
                             diff_pair):
    """Prepare a FileResult object for a diff result.

    Create the FileResult object and set some required data. Note that the file
    type should be recorded in advance using the _RecordFileType() method.

    Args:
      path: The file path.
      analysis_result: The AnalysisResult to which this FileResult should be
                       added.
      result_type: The result type.
      diff_pair: The DiffPair this result applies to.

    Returns:
      The newly created FileResult object.
    """

    return self._PrepareFileResult(path, analysis_result, result_type, None,
                                   diff_pair)

  def _PrepareDescriptiveFileResult(self, path, analysis_result,
                                    descriptive_trigger):
    """Prepare a FileResult object for a descriptive result.

    Create the FileResult object and set some required data. Note that the file
    type should be recorded in advance using the _RecordFileType() method.

    Args:
      path: The file path.
      analysis_result: The AnalysisResult to which this FileResult should be
                       added.
      descriptive_trigger: The trigger this result applies to.

    Returns:
      The newly created FileResult object.
    """

    return self._PrepareFileResult(
        path, analysis_result, wheelbarrow_pb2.DESCRIPTIVE, descriptive_trigger)

  def _PrepareFileResult(self, path, analysis_result, result_type,
                         descriptive_trigger=None, diff_pair=None):
    """Prepare a FileResult object.

    If this analysis is part of a suite, either record the result as part of the
    suite using the suite manager, or get an existing file result from the suite
    manager.

    Args:
      path: The file path.
      analysis_result: The AnalysisResult to which this FileResult should be
                       added.
      result_type: The result type.
      descriptive_trigger: The trigger this result applies to.
      diff_pair: The DiffPair this result applies to.

    Returns:
      The newly created FileResult object.

    Raises:
      FatalAnalysisError if it is called with a weird argument combination.
    """

    if descriptive_trigger is None and diff_pair is None:
      raise analysis.FatalAnalysisError(
          ('Fatal error in FileAnalyzer while preparing result for %s: '
           'descriptive trigger or diff pair should not be None' % path))

    if self._analysis_suite != FileAnalyzer._NO_SUITE:
      # First try the suite manager.
      trigger_or_diff_pair = diff_pair if diff_pair else descriptive_trigger
      file_result = FileResultSuiteManager.GetSuiteResult(
          self._analysis_suite, trigger_or_diff_pair, path)
      if file_result:
        return file_result

    if self._analysis_suite != FileAnalyzer._NO_SUITE:
      analysis_result.analysis_name = self._analysis_suite

    # Add a file result.
    result = analysis_result.results.add()
    file_result = None
    if self._analysis_suite == 'package':
      file_result = result.package_results.add()
    else:
      file_result = result.file_system_results.add()

    # Set the state(s).
    if descriptive_trigger is not None:
      # Set the state of the descriptive analysis.
      state = file_result.states.add()
      state.trigger = descriptive_trigger
    elif diff_pair is not None:
      # Set the two states of the diff analysis.
      state_before = file_result.states.add()
      state_before.trigger = diff_pair.before
      state_after = file_result.states.add()
      state_after.trigger = diff_pair.after

    # Set path, result type and file type.
    file_result.path = path
    file_result.type = result_type
    file_result.file_type = self._GetFileType(path)

    # Record any new suite result.
    if self._analysis_suite != FileAnalyzer._NO_SUITE:
      FileResultSuiteManager.AddFileResult(
          self._analysis_suite, trigger_or_diff_pair, path, file_result)

    return file_result

  @staticmethod
  def _ComputeStringHash(string, hash_function):
    """Compute the hash of a string.

    Args:
      string: A string.
      hash_function: A hash function.

    Returns:
      The hash of the input string.
    """

    hash_instance = hash_function()
    hash_instance.update(string)
    return hash_instance.hexdigest()
