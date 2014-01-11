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
"""Broker initializer base class."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


class Error(Exception):
  pass


class InitializationError(Error):
  pass


class NoPackageError(Error):
  pass


class BrokerInitializer(object):
  """Base class for a broker initializer.

  A broker initializer is in charge of getting information such as package name
  and analysis output directory. It also performs some other initialization
  functions (e.g., log configuration). Subclasses should implement method
  InitializeBroker(), which should return a "context" object. The context should
  have at least a package_descriptor attribute, which should contain a
  wheelbarrow_pb2.Package for the application under test.
  """

  def InitializeBroker(self):
    raise NotImplementedError

