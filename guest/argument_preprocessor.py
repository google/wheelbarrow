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
"""Preprocess analysis arguments.

Some analysis arguments are not known until the package under test is extracted.
On the other hand, analyzers expect specific analysis arguments. This module is
in charge of converting analysis arguments as described by analysis descriptors
to arguments that can be used by analyzers.
"""

import codecs
import glob
import os
import re
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


def PreprocessArgument(argument, extract_dir):
  """Preprocess an analysis argument.

  Args:
    argument: An analysis argument.
    extract_dir: The directory where the package is extracted.

  Returns:
    An analyzer argument.
  """

  has_prefix = argument.prepend_extract_dir
  prefix = extract_dir if has_prefix else ''
  file_paths = []
  excluded_patterns = None
  if argument.excluded_patterns:
    excluded_patterns = re.compile('|'.join(argument.excluded_patterns))

  for path_argument in argument.string_args:
    complete_path_argument = os.path.join(prefix, path_argument)
    expanded_path_arguments = glob.glob(complete_path_argument)
    for expanded_path_argument in expanded_path_arguments:
      if argument.recursive_file_walk:
        for (dir_path, _, file_names) in os.walk(codecs.encode(expanded_path_argument, 'utf-8')):
          for file_name in file_names:
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
              rel_path = (os.path.relpath(file_path, prefix) if has_prefix
                          else file_path)
              if excluded_patterns and excluded_patterns.match(rel_path):
                continue
              file_paths.append((file_path, rel_path))
      else:
        file_paths.append((expanded_path_argument, expanded_path_argument))

  return file_paths
