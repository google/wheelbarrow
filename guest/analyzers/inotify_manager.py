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
"""Inotify manager."""

from collections import Counter
import os.path
import time

import pyinotify


class RecordingProcessEvent(pyinotify.ProcessEvent):
  """Class to process an event by recording which path was affected by it."""

  def __init__(self):
    self._affected_paths = {}

  # We have to override this function, but the naming style is not right.
  def process_default(self, event):   # pylint: disable=g-bad-name
    """Process an event.

    Each file that is affected has a counter which measures how many times it
    was affected by an event. This function increments that counter.

    Args:
      event: A pyinotify.Event.
    """

    path = (event.path if os.path.isfile(event.path)
            else os.path.join(event.path, event.name))
    if os.path.isfile(path):
      event_name = event.maskname
      if event_name not in self._affected_paths:
        self._affected_paths[event_name] = Counter()
      self._affected_paths[event_name][path] += 1

  def GetAffectedPaths(self, event_name):
    """Get a counter for the paths affected by an event.

    Args:
      event_name: The name of an inotify event, as a string.

    Returns:
      A counter of the number of times each path was affected by an event. Note
      that unaffected paths are not in the counter.
    """

    return self._affected_paths.get(event_name)


class InotifyManager(object):
  """Manager for inotify notifier."""

  _process_event = None
  _watch_manager = None
  _notifier = None

  def __init__(self):
    if InotifyManager._process_event is None:
      InotifyManager._process_event = RecordingProcessEvent()
      InotifyManager._watch_manager = pyinotify.WatchManager()
      InotifyManager._notifier = pyinotify.ThreadedNotifier(
          self._watch_manager, self._process_event)
      InotifyManager._notifier.start()

  @staticmethod
  def GetAffectedPaths(event_names):
    """Read the counters of affected paths.

    The ThreadedNotifier that we use periodically polls the inotify file
    descriptor in a separate thread. We wait a bit to make sure that the other
    thread picks up the latest events.

    Args:
      event_names: A list of inotify event names (list of strings).

    Returns:
      A counter of affected paths counting how many times a path was affected by
      a given event.
    """

    time.sleep(0.1)
    result = Counter()
    for event_name in event_names:
      counter_for_one_event = InotifyManager._process_event.GetAffectedPaths(
          event_name)
      if counter_for_one_event is not None:
        result += counter_for_one_event
    return result

  @staticmethod
  def StartWatchingPath(path, event_names, recursive=True):
    """Start watching a path.

    Args:
      path: A file or directory path.
      event_names: A list of event names (list of strings).
      recursive: For directories, setting this as True causes subdirectories to
                 be watched as well.
    """

    InotifyManager._watch_manager.add_watch(
        path, InotifyManager._MakeMaskFromEventNames(event_names),
        rec=recursive)

  @staticmethod
  def Close():
    InotifyManager._notifier.stop()

  @staticmethod
  def _MakeMaskFromEventNames(event_names):
    """Make an event mask from a list of events.

    Args:
      event_names: A list of inotify event names (list of strings).

    Returns:
      An event mask.
    """

    mask = 0
    for event_name in event_names:
      mask |= pyinotify.EventsCodes.FLAG_COLLECTIONS['OP_FLAGS'][event_name]
    return mask
