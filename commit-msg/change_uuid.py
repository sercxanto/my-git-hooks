#!/usr/bin/python
# vim: set fileencoding=utf-8 :
"""
    change_uuid.py

    Add uuid to git commit message"""
#
#    Copyright (C) 2013 Georg Lutz <georg AT NOSPAM georglutz DOT de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import hashlib
import logging
import os
import re
import sys
import uuid

UUID_PREFIX = "Change-UUID:"


def read_uuid(commitfile):
    '''Returns the uuid value, empty string if not found.
    commitfile is an file object'''
    prog = re.compile("^" + UUID_PREFIX + "\s*(?P<uuid>[a-f0-9]{32})\s*$")

    commitfile.seek(0, os.SEEK_SET)
    for line in commitfile:
        match = prog.match(line)
        if match != None and len(match.groups()) == 1:
            uuid_ = match.group("uuid")
            return uuid_
    return ""


def write_uuid(commitfile, uuid_):
    '''Writes the uuid at the end of commitmessage file
    '''
    commitfile.seek(0, os.SEEK_END)
    commitfile.write("\n" + UUID_PREFIX + " " + uuid_)


def calc_digest(commitfile):
    '''Calculate hash for given commitfile.
    Returns hash as string in lowercase hex notation.
    Returns empty string if message is empty.'''
    commitfile.seek(0, os.SEEK_SET)
    is_empty = True
    hasher = hashlib.sha256()
    for line in commitfile:
        # This isn't meant to mimic git-stripspace. We just want to make sure
        # 1. to stop on empty messages
        # 2. to hash only the message text not filenames in comment section
        if len(line.rstrip()) > 0 and line[0] != "#":
            is_empty = False
            hasher.update(line)
    if is_empty:
        return ""
    else:
        return hasher.hexdigest().lower()[0:10]


class UuidStore():
    '''Stores UUIDs together with their digest in filesystem.
    Idea:
      * Store the information encoded in file names. The file itself is empty.
        -> no overhead, no locking
      * Store 3 informations : 10 char digest, 32 char uuid, timestamp of last
        use as mtime.
      * Format: "10chardigest_uuid",
        e.g. "abcdef123_0123456789abcdef0123456789abcdef".
      * Store in users home directory.
      * Delete information after 10 minutes.
      '''

    def __init__(self):
        self._dirty = True
        self._path = os.path.expanduser(os.path.join(
            "~", ".git_hooks", "_data", "change_uuid"))
        self._max_age = 10 * 60 # in seconds
        self._match_prog = re.compile(
                "(?P<digest>[a-f0-9]{10})_(?P<uuid>[a-f0-9]{32})")


    def _calc_file_path(self, uuid_, digest):
        '''Returns the file path for a given uuid/digest combination'''
        return os.path.join(self._path, digest + "_" + uuid_)


    def _parse_uuid_digest(self, filename):
        '''Returns dict constisting of uuid and digest'''
        result = {"uuid": "", "digest": ""}
        match = self._match_prog.match(filename)
        if match != None and len(match.groups()) == 2:
            result["uuid"] = match.group("uuid")
            result["digest"] = match.group("digest")
        return result
    

    def _cleanup(self):
        '''Cleanup old uuids'''
        if not os.path.exists(self._path) or not self._dirty:
            return
        logging.info("Doing cleanup.")
        files = os.listdir(self._path)
        delta = datetime.timedelta(seconds=self._max_age)
        delete_before = datetime.datetime.now() - delta

        for entry in files:
            file_path = os.path.join(self._path, entry)
            file_mtime = datetime.datetime.fromtimestamp(
                    os.stat(file_path).st_mtime)
            if file_mtime < delete_before:
                logging.info("  Delete "+ file_path)
                os.remove(file_path)
            
        self._dirty = False


    def record_uuid(self, uuid_, digest):
        '''Stores uuid for given digest'''
        self._cleanup()
        if not os.path.exists(self._path):
            os.makedirs(self._path)
        file_ = open(self._calc_file_path(uuid_, digest), "w+")
        file_.close()
        self._dirty = True


    def get_uuid_for_digest(self, digest):
        '''Returns uuid for given digest'''
        self._cleanup()
        if not os.path.exists(self._path):
            return ""
        files = os.listdir(self._path)
        for file_ in files:
            entry = self._parse_uuid_digest(file_)
            if entry["digest"] == digest:
                return entry["uuid"]
        return ""


def run_hook(commitmsg):
    '''Actually run the hook logic, the real main function'''
    if not os.path.exists(commitmsg):
        print "Commit message file \"" + commitmsg + "\" does not exist. Abort."
        sys.exit(1)
    
    commitfile = open(commitmsg, "rw+")
    uuid_ = read_uuid(commitfile)
    if len(uuid_) == 0:
        digest = calc_digest(commitfile)
        if len(digest) == 0:
            logging.info("Empty message detected. Do nothing")
            commitfile.close()
            sys.exit(0)
        logging.info("No UUID found in commit message, digest for message is " + digest)
        uuid_store = UuidStore()

        uuid_ = uuid_store.get_uuid_for_digest(digest)
        if len(uuid_) == 0:
             # hex: ommit "-" as searchtools may interpret it as metachar
            uuid_ = uuid.uuid4().hex.lower()
            logging.info("No UUID found for digest, generated new one: " + uuid_)
        else:
            logging.info("Found UUID for digest: " + uuid_)
        
        logging.info("Writing UUID to commit message file \"" + commitmsg + "\"")
        write_uuid(commitfile, uuid_)
        uuid_store.record_uuid(uuid_, digest)
    else:
        logging.info("Found existing UUID " + uuid_ + ". Do nothing.")

    sys.exit()
    commitfile.close()
    sys.exit(0)


def main():
    '''main function'''

    description =  """
When installed as git hook this scripts adds a line with a random UUID at the
end of the commit message.

Commit which are done in the last 10 minutes and have the same message share
the same UUID.
"""
    parser = argparse.ArgumentParser(
            description=description)
    parser.add_argument("messagefile", type=str, nargs="?",
            help="file holding commit message")
    parser.add_argument('--about', dest='about', action='store_true',
            help='Message to display in git-hooks script')
    parser.add_argument("-v", '--verbose', dest='verbose', default=False,
            action="store_true",
            help="Print out additional (debug) info")
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s")
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    if args.about:
        print "Add uuid to git commit message"
        sys.exit(0)
    if args.messagefile == None:
        parser.print_help()
        sys.exit(0)
    run_hook(args.messagefile)


if __name__ == "__main__":
    main()
