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
"""Trigger management module."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


from common import wheelbarrow_pb2


class Error(Exception):
  pass


class TriggerError(Error):
  pass


class NoNextTrigger(Error):
  pass


class Trigger(object):
  """Base class for all triggers.

  Subclasses should override methods GetTriggerId() and RunTrigger().
  """

  def GetTriggerId(self):
    """Get the ID of this trigger, as defined in the application protobuf."""

    raise NotImplementedError

  def RunTrigger(self):
    """Run this trigger."""

    raise NotImplementedError


# Base classes for all the triggers types defined in the application protobuf.
# When a new trigger is added to the protobuf, a new base class should be
# created here.
# Subclasses should only implement RunTrigger().
class Extract(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.EXTRACT


class Install(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.INSTALL


class StartService(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.START_SERVICE


class StopService(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.STOP_SERVICE


class RunBinaries(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.RUN_BINARIES


class Remove(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.REMOVE


class Purge(Trigger):
  def GetTriggerId(self):
    return wheelbarrow_pb2.PURGE


class TriggerManager(object):
  """Base class for a trigger manager.

  A trigger manager is in charge of doing any setup needed by the package
  manager being used, as well as setting up and calling each trigger. Subclasses
  should implement:
    - SetUpTriggersAndMetadata(): perform trigger setup and set the package
                                  metadata (name, version, etc.).
    - _GetNextTrigger(): get the next trigger to be executed.
  """

  _package_extract_dir = None

  def SetUpTriggersAndMetadata(self, package_descriptor):
    """Perform setup for the trigger manager and extract package metadata.

    Args:
      package_descriptor: A Package message.
    """

    raise NotImplementedError

  def _GetNextTrigger(self):
    """Get the next trigger to be executed.

    This method should behave the same way as next() for an iterator, raising a
    NoNextTrigger error when no next trigger is available.
    """

    raise NotImplementedError

  def RunNextTrigger(self):
    """Run the next trigger.

    Returns:
      The current trigger ID if performing the trigger went well, None if there
      is no trigger to perform.
    """

    try:
      trigger = self._GetNextTrigger()
      trigger.RunTrigger()
      return trigger.GetTriggerId()
    except NoNextTrigger:
      return None

  @staticmethod
  def GetPackageExtractDir():
    """Get the directory where the package is extracted.

    Returns:
      The path to the directory where the package is extracted.
    """

    return TriggerManager._package_extract_dir

  @staticmethod
  def _SetPackageExtractDir(package_extract_dir):
    TriggerManager._package_extract_dir = package_extract_dir
