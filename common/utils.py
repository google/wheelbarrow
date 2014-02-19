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
"""Common utility functions."""

import logging
import os
import sys

WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)

from google.protobuf import text_format
from google.protobuf.message import DecodeError
from google.protobuf.message import EncodeError


def LoadFileToString(file_path, file_size_limit=-1):
  """Load the contents of a file to a string.

  Args:
    file_path: A file path.
    file_size_limit: The maximum number of bytes to read from the file, or -1
                     for no limit.

  Returns:
    A string with the contents of the file whose path is given as input if all
    goes well, None otherwise.
  """

  if file_size_limit >= 0 and os.stat(file_path).st_size > file_size_limit:
    logging.error('File %s is bigger than %d bytes.', file_path,
                  file_size_limit)
    return None
  try:
    if os.path.islink(file_path):
      linked_path = os.readlink(file_path)
      file_path = (linked_path if os.path.isabs(linked_path)
                   else os.path.join(os.path.dirname(file_path), linked_path))
    in_file = open(file_path)
    file_contents_string = in_file.read(file_size_limit)
    in_file.close()
    return file_contents_string
  except (IOError, OSError) as err:
    logging.error('Unable to read file %s to string: %s', file_path, err)
    return None


def ParseFileToProtobuf(file_path, protobuf, file_size_limit=-1, text=None):
  """Parse a file containing a protobuf.

  Args:
    file_path: The path to a file containing a protobuf.
    protobuf: A destination protobuf.
    file_size_limit: The maximum number of bytes to read from the file, or -1
                     for no limit.
    text: True if the file contains an ASCII protobuf.

  Returns:
    True if the protobuf was read correctly.
  """

  if text is None:
    text = not file_path.endswith('.dat')
  file_contents_string = LoadFileToString(file_path, file_size_limit)
  if file_contents_string is None:
    logging.error('Unable to read file %s while trying to parse it as protobuf '
                  'message %s.', file_path, type(protobuf))
    return False

  try:
    if text:
      text_format.Merge(file_contents_string, protobuf)
    else:
      protobuf.MergeFromString(file_contents_string)
    return True
  except (DecodeError, text_format.ParseError) as err:
    logging.error('Error while parsing file %s to protobuf message %s: %s',
                  file_path, type(protobuf), err)
    return False


def WriteProtobufToFile(protobuf, file_path, text=None, add_extension=False):
  """Write a protobuf to a file, adding an extension if requested.

  Args:
    protobuf: A protocol buffer.
    file_path: The path to the destination file.
    text: True if the protobuf should be written in ASCII format.
    add_extension: True if a file extension should be added (.txt for ASCII,
                   .dat for binary).

  Returns:
    True if the protobuf was written correctly.
  """

  if text is None:
    text = not file_path.endswith('.dat')

  if add_extension:
    extension = '.txt' if text else '.dat'
    file_path = '%s%s' % (file_path, extension)

  encoded_protobuf = None
  try:
    encoded_protobuf = (text_format.MessageToString(protobuf) if text
                        else protobuf.SerializePartialToString())
  except EncodeError as err:
    logging.error('Could not encode protobuf when writing to file %s: %s',
                  file_path, err)
    return False
  try:
    out_file = open(file_path, 'w')
    out_file.write(encoded_protobuf)
    out_file.close()
    return True
  except (IOError, OSError) as err:
    logging.error('Could not write protobuf to file %s: %s', file_path, err)
    return False
