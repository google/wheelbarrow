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
"""The analysis broker.

     Usage: %s
       [-o|--outdir <output directory>]
       [--textout]
       [--nfs <path to NFS configuration file>]
       [--package <name of an application package>]
"""

from collections import namedtuple
import gflags
import logging
import os
import signal
import sys
import time

WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2
from common.utils import WriteProtobufToFile
from guest import broker_initializer
from guest import deb_triggers
from guest.analysis import FatalAnalysisError
from guest.analyzers.inotify_manager import InotifyManager
from guest.file_system_analysis_loader import FileSystemAnalysisLoader
from guest.nfs_broker_initializer import NfsBrokerInitializer
from guest.triggers import TriggerError


FLAGS = gflags.FLAGS

gflags.DEFINE_string('outdir', './', 'The output directory for the analysis '
                    'results.', short_name='o')
gflags.DEFINE_boolean('textout', False, 'Activate text output for analysis '
                     'results. By default, the results are output to a binary '
                     'protocol buffer.', short_name='t')
gflags.DEFINE_string('nfs', "/mnt/broker/analysis.config", 'The path to an NFS config file.',
                     short_name='n')
gflags.DEFINE_string('package', None, 'The name of an application package to be '
                    'analyzed.', short_name='p')


_ANALYSIS_DESCRIPTORS_PATH = WHEELBARROW_HOME + '/guest/analyses/*'
_DEFAULT_TIMEOUT = 1100


class Error(Exception):
  pass


class BrokerError(Error):
  pass


class Broker(object):
  """An analysis broker."""

  def __init__(self):
    self._application_result = wheelbarrow_pb2.ApplicationResult()

  def StartAnalysis(self):
    """Start the analysis.

    Raises:
      BrokerError: If something goes wrong during initialization.
    """

    try:
      self._Initialize()
    except broker_initializer.Error as err:
      error = 'Could not initialize broker: %s' % str(err)
      logging.error(error)
      raise BrokerError(error)

    package_descriptor = self._context.package_descriptor
    self._application_result.package.CopyFrom(package_descriptor)

    signal.signal(signal.SIGALRM, self.AlarmHandler)
    signal.alarm(self._GetTimeout())
    error = self._PerformTimedAnalysis()
    signal.alarm(0)

    self._Finalize(error)

  def _PerformTimedAnalysis(self):
    """Perform the actual analysis.

    The calling method should set a timeout on this.

    Returns:
      The error string if anything went wrong, None otherwise.
    """

    logging.info('Starting analysis.')

    analysis_loaders = Broker._PrepareAnalysisLoaders()
    analyses = Broker._LoadAnalyses(analysis_loaders)

    error = None
    try:
      trigger_manager = deb_triggers.DebTriggerManager()
      trigger_manager.SetUpTriggersAndMetadata(self._application_result.package)
      while True:
        current_trigger = trigger_manager.RunNextTrigger()
        if current_trigger is None:
          break
        for analysis in analyses:
          analysis.RunAnalysis(current_trigger)
    except (FatalAnalysisError, TriggerError) as err:
      logging.error('Error while running triggers and analyses: %s', err)
      error = str(err)
      if not error:
        # Bad situation: we have an error but we don't know what it is.
        error = 'Unknown error.'

    if not error:
      try:
        for analysis in analyses:
          analysis.AddResults(self._application_result)
      except FatalAnalysisError as err:
        logging.error('Error while adding analysis results: %s', err)
        error = str(err)
        return error

    return error

  def _Initialize(self):
    """Initialize the analysis and set the analysis context.

    This includes a factory for a BrokerInitializer. It looks for an NFS setup.
    If one is not specified, it looks for a package name on the command line. If
    nothing is found, it fails. The context attribute is set.

    Raises:
      broker_initializer.Error if no package was specified.
    """

    logging.info('Initializing analysis.')
    if FLAGS.nfs:
      initializer = NfsBrokerInitializer(FLAGS.nfs)
      self._context = initializer.InitializeBroker()
    elif FLAGS.package:
      # Get the package name from the command line.
      package_descriptor = wheelbarrow_pb2.Package()
      package_descriptor.name = FLAGS.package
      context = namedtuple('cl', 'package_descriptor')
      self._context = context(package_descriptor, None)
    else:
      logging.error('No package was specified.')
      raise broker_initializer.Error('No package was specified.')

  def _GetTimeout(self):
    """Get the analysis timeout using the analysis context.

    Returns:
      The analysis timeout.
    """

    try:
      return self._context.config.timeout
    except AttributeError:
      return _DEFAULT_TIMEOUT

  def _Finalize(self, error):
    """Finalize the analysis.

    Args:
      error: An error description if something went wrong, None otherwise.

    Raises:
      BrokerError: If something went wrong during the analysis.
    """

    Broker._FinalizeApplicationResult(self._application_result.package, error)
    context_type = type(self._context).__name__
    (out_dir, text_out) = ((self._context.config.output_dir,
                            self._context.config.text_output)
                           if context_type == 'nfs'
                           else (FLAGS.outdir, FLAGS.textout))
    self._WriteApplicationResultToFile(out_dir, text_out)
    if context_type == 'nfs':
      os.remove(self._context.pending_descriptor_path)
    InotifyManager.Close()
    if error:
      raise BrokerError(error)

  @staticmethod
  def _PrepareAnalysisLoaders():
    """Prepare analysis loaders.

    At the moment, only loading analyses from the file system is supported. In
    the future we may want to load analyses from other places.

    Returns:
      A list of analysis loaders (subclasses of AnalysisLoader).
    """

    path = _ANALYSIS_DESCRIPTORS_PATH
    return [FileSystemAnalysisLoader([path])]

  @staticmethod
  def _LoadAnalyses(analysis_loaders):
    """Load analyses using analysis loaders.

    Args:
      analysis_loaders: A list of analysis loaders (subclasses of
                        AnalysisLoader).

    Returns:
      A list of Analysis objects.
    """

    analyses = []
    for analysis_loader in analysis_loaders:
      analyses += analysis_loader.LoadAnalyses()
    return analyses

  @staticmethod
  def _FinalizeApplicationResult(package_descriptor, error):
    """Finalize an application result by updating its package descriptor.

    Args:
      package_descriptor: A wheelbarrow_pb2.Package.
      error: An error description if something went wrong, None otherwise.
    """

    logging.info('Finalizing application result.')
    if error:
      package_descriptor.status = wheelbarrow_pb2.Package.FAILED
      package_descriptor.error = error
    else:
      package_descriptor.status = wheelbarrow_pb2.Package.DONE
    package_descriptor.analysis_end = int(time.time())

  def _WriteApplicationResultToFile(self, out_dir, text_out):
    """Write a wheelbarrow_pb2.ApplicationResult to a file.

    Args:
      out_dir: A directory where the output should be written.
      text_out: True if the file should be written in ASCII text, False if it
      should be written in binary.
    """

    logging.info('Writing application result to file.')
    out_file_name = ('%s-%s-%s'
                     % (self._application_result.package.name,
                        self._application_result.package.version,
                        self._application_result.package.architecture))
    out_file_path = os.path.join(out_dir, out_file_name)
    if not WriteProtobufToFile(self._application_result, out_file_path,
                               text_out, True):
      logging.error('Could not write application result file %s.',
                    out_file_path)

  def AlarmHandler(self, unused_signalnum, unused_frame):
    """Handle a sigalrm signal by recording the timeout to the result file."""

    error = 'Analysis timed out.'
    logging.error(error)
    self._Finalize(error)


def main(argv):
  logging.root.setLevel(logging.INFO)

  broker = Broker()
  try:
    broker.StartAnalysis()
    logging.info('Start analysis completed')
  except BrokerError as err:
    logging.error('Broker could not complete the analysis: %s', err)
    return 1


if __name__ == '__main__':
  logging.info('Logging starting')
  main(sys.argv)
