#!/bin/bash
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

# Launch analysis broker on the VM.

NFS_PATH=/mnt/broker
export WHEELBARROW_HOME=${NFS_PATH}/wheelbarrow
BROKER=${WHEELBARROW_HOME}/guest/broker.py

# Avoid prompts during install.
export DEBIAN_FRONTENT=noninteractive

# Start analysis.
sudo -E "${BROKER}" --nfs "${NFS_PATH}/analysis.config"

poweroff
