#!/bin/bash
#
# record_commit.sh
#
# Stores a backlog of all commits
#
# Copyright (C) 2013 Georg Lutz <georg AT NOSPAM georglutz DOT de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#

set -eu
function error_handler()
{
    echo "Error in ${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}:${BASH_COMMAND}"
}
trap error_handler ERR


function record_commit()
{
    digest=$(git show -s --pretty=format:%h)
    timestamp=$(date +%Y%m%d_%H%M%S)
    rel_folder=$(date +%Y/%m)

    repo_name=$(git config --get remote.origin.url | awk -F/ '{print $NF}' | awk -F: '{print $NF}')
    if [ -z "$repo_name" ]; then
        repo_name=$(basename $(git rev-parse --show-toplevel))
    fi

    dir="$HOME/.git_hooks/_data/record_commit/$rel_folder"
    file_name="${timestamp}_${repo_name}_${digest}"

    mkdir -p $dir

    git log -1 --name-status HEAD > $dir/$file_name
}

if [[ $# -eq 1 && $1 == "--about"  ]]; then
    echo "Stores a backlog of all commits"
else
    record_commit
fi

