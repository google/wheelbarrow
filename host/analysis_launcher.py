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
"""Start package analyses using the specified VM image.

     Usage: %s
       -i|--image <VM image>
       [-m|--memory <memory size>]
       [-t|--timeout <timeout>]
       [--batchfile <path to batch package descriptor>]
       [-h|--nfshost <path to an NFS share on the host]
       [-g|--nfsguest <path to an NFS share on the guest]
       [--textout]
       [-p|--processes <maximum number of concurrent VM processes>]
       [--snapshot]
       [--updatebroker]
"""

import logging
from multiprocessing import Pool
import os
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

import gflags
from host.nfs_analysis_setup_agent import NfsAnalysisSetupAgent
from host.scoring.result_directory_scorer import ScoreResultDirectory
import host.vm_launcher

FLAGS = gflags.FLAGS

gflags.DEFINE_string('image', None, 'The VM image which should be used.',
                     short_name='i')
gflags.MarkFlagAsRequired('image')
gflags.DEFINE_integer('memory', 4096, 'Amount of physical memory for the VM.',
                      short_name='m')
gflags.DEFINE_integer('timeout', 120, 'VM timeout, after which it will be '
                      'killed.', short_name='t')
gflags.DEFINE_string('batchfile', None, 'A file containing a description of '
                     'packages to be downloaded.', short_name='b')
gflags.DEFINE_string('nfshost', None, 'The path to an NFS share on the host.',
                     short_name='h')
gflags.DEFINE_string('nfsguest', None, 'The path to an NFS share on the guest.',
                     short_name='g')
gflags.DEFINE_boolean('textout', False, 'Activate text output for analysis '
                      'results. By default, the results are output to a binary '
                      'protocol buffer.', short_name='a')
gflags.DEFINE_integer('processes', 1,
                      'Number of concurrent analysis processes.',
                      short_name='p')
gflags.DEFINE_boolean('snapshot', True, 'Activate snapshot mode, which avoids '
                      'writing modifications to the VM image.', short_name='s')
gflags.DEFINE_boolean('updatebroker', False, 'Update the broker package on the '
                      'VM image before proceeding with the analysis.',
                      short_name='u')


_SCORE_DIR = 'scores'


def main(argv):
  """Allow calling scoring independent of analysis run."""

  argv = FLAGS(argv)
  logging.root.setLevel(logging.INFO)
  logging.info(argv)
  job_count = 1
  if FLAGS.batchfile:
    if FLAGS.nfshost and FLAGS.nfsguest:
      logging.info(FLAGS.image)
      setup_agent = NfsAnalysisSetupAgent(FLAGS.nfshost, FLAGS.nfsguest,
                                          FLAGS.timeout, FLAGS.textout, False,
                                          FLAGS.updatebroker, FLAGS.image)
      job_count = setup_agent.SetUpAnalysis(FLAGS.batchfile)
      if job_count == NfsAnalysisSetupAgent.ERROR:
        logging.error('NFS analysis setup has failed.')
        return 1
    else:
      logging.error('A batch package descriptor file was provided without NFS '
                    'share paths.')
      print gflags.FLAGS
      return 1
    if job_count == 0:
      logging.error('No packages from the regexp you specified')
      print "Update this file", FLAGS.batchfile
      return 1

  logging.info('Starting analysis of %d applications...', job_count)
  processes = FLAGS.processes if job_count >= FLAGS.processes else job_count
  pool = Pool(processes=processes)
  logging.info('Flags are::::::::::::::')
  logging.info(FLAGS.image)
  cmd = host.vm_launcher.MakeVmCommand(
      FLAGS.image, FLAGS.memory, FLAGS.snapshot)

  logging.info(cmd)
  for unused_i in range(job_count):
    pool.apply_async(host.vm_launcher.StartVm, args=(cmd, FLAGS.timeout))
  pool.close()
  pool.join()

  logging.info('Complete run proceeding to scoring')
  if FLAGS.nfshost:
    logging.info('Scoring...')
    logging.info(FLAGS.nfshost)
    logging.info(NfsAnalysisSetupAgent.OUTPUT_DIR)
    logging.info(_SCORE_DIR)
    logging.info(FLAGS.textout)
    ScoreResultDirectory(
        os.path.join(FLAGS.nfshost, NfsAnalysisSetupAgent.OUTPUT_DIR),
        os.path.join(FLAGS.nfshost, _SCORE_DIR), FLAGS.textout)


if __name__ == '__main__':
  main(sys.argv)
