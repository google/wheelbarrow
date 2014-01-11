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
"""Utility functions for tests."""

import sys
import os.path
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from google.protobuf import text_format


def CheckResultProtobufFromFile(self, protobuf, reference_file_path,
                                reference_protobuf):
  """Compare a protocol buffer to an expected value read from file.

  Args:
    self: A TestCase object.
    protobuf: The protobuf to be checked.
    reference_file_path: The path to the file containing the reference protobuf.
    reference_protobuf: An instance of the object to which the reference
                        protobuf should be read.
  """

  result_file = open(reference_file_path)
  expected_result = result_file.read()
  result_file.close()
  text_format.Merge(expected_result, reference_protobuf)
  str1 = text_format.MessageToString(protobuf, as_one_line=True)
  str2 = text_format.MessageToString(reference_protobuf, as_one_line=True)
  self.assertEqual(str1, str2)
