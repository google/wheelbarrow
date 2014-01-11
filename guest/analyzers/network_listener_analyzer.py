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
"""Network listener analyzer."""

import logging
import os.path
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2
from guest import guest_utils
from guest.analysis import RecoverableAnalysisError
from guest.analyzers.file_analyzer import FileAnalyzer
from guest.analyzers.trigger_map_analyzer import TriggerMapAnalyzer


class NetworkListenerAnalyzer(TriggerMapAnalyzer):
  """A network listener analyzer."""

  _NETSTAT = '/bin/netstat'
  _NETSTAT_COMMAND = ['sudo', _NETSTAT, '-anp']
  # We keep track of established connections, but this is not currently used.
  _LISTEN_EXPRESSION = (r'(\S+)\s+\S+\s+\S+\s+(\S+):(\d+)\s+(\S+):([^\s^:]+)\s+'
                        r'(LISTEN|ESTABLISHED)?\s+(\d+).+')

  def RunAnalysis(self, trigger, unused_argument, unused_suite):
    """Run a network listener analysis."""

    netstat_results = None
    try:
      netstat_results = guest_utils.ExecuteCommandAndMatch(
          NetworkListenerAnalyzer._NETSTAT_COMMAND,
          NetworkListenerAnalyzer._LISTEN_EXPRESSION)
    except guest_utils.CommandMatchingError as e:
      error = 'Could not execute netstat -anp: %s' % str(e)
      logging.error(error)
      raise RecoverableAnalysisError(error)
    package_binaries = set('/%s' % s for s in FileAnalyzer.GetBinaries())
    pid_to_path_map = None
    try:
      pid_to_path_map = guest_utils.FindPidsForBinaries(package_binaries)
    except guest_utils.PidMatchingError as e:
      error = ('Could not find pids for binaries %s: %s'
               % (str(package_binaries), str(e)))
      logging.error(error)
      raise RecoverableAnalysisError(error)
    self._analysis_results[trigger] = []
    for netstat_result in netstat_results:
      if netstat_result[6] in pid_to_path_map:
        netstat_result_list = list(netstat_result)
        netstat_result_list.append(pid_to_path_map[netstat_result[6]])
        self._analysis_results[trigger].append(netstat_result_list)

  def AddDescriptiveResults(self, descriptive_trigger, analysis_result):
    descriptive_results = self._GetAnalysisResultForTrigger(descriptive_trigger)
    for descriptive_result in descriptive_results:
      is_udp = 'udp' in descriptive_result[0]
      if (descriptive_result[1] != '127.0.0.1'
          and (is_udp or descriptive_result[5] == 'LISTEN')):
        result = analysis_result.results.add()
        network_result = result.network_results.add()
        network_result.type = wheelbarrow_pb2.DESCRIPTIVE
        state = network_result.states.add()
        state.trigger = descriptive_trigger
        local_address = descriptive_result[1]
        if ':' in local_address:
          state.local_ip6address = local_address
        else:
          state.local_ip4address = local_address
        state.local_port = descriptive_result[2]
        foreign_address = descriptive_result[3]
        if ':' in foreign_address:
          state.foreign_ip6address = foreign_address
        else:
          state.foreign_ip4address = foreign_address
        state.foreign_port = descriptive_result[4]
        state.is_udp = is_udp
        state.process_path = descriptive_result[7]
