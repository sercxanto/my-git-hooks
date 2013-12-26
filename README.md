Installation
============

Download the git-hooks wrapper script from
https://github.com/icefox/git-hooks and install it in your $PATH, e.g. by

    wget https://raw.github.com/icefox/git-hooks/master/git-hooks -O ~/bin/git-hooks; chmod u+x ~/bin/git-hooks

Then install this repository in ~/.git\_hooks:

    git clone https://github.com/sercxanto/my-git-hooks ~/.git_hooks
    git config --global init.templatedir ~/.git_hooks/_templatedir

Now new or freshly cloned repositories contain the hooks defined in
\_templatedir (which point to the git-hooks wrapper script). To make use git-hooks in already existing repositories run git-hooks --install in each of these:

    find ~/src -name ".git" -type d -exec bash -c 'cd {}; git-hooks --install' \;


change\_uuid.py hook
====================

Inspired by gerrits [commitmsg
hook](https://gerrit.googlesource.com/gerrit/+/master/gerrit-server/src/main/resources/com/google/gerrit/server/tools/root/hooks/commit-msg).
But unlike the gerrit hook this script generates purely random uuids independed
of the commit history.

You can track changes across cherry-picks, rebases and merges.

change\_uuid also helps to track changes in a project
consisting of multiple repositories (cross repo changes).

To accomplish this all identical commit messages of the last 10 minutes share
the same uuid. There might be corner cases where this does not work, e.g. when
commiting to two different projects with just "git commit -m bugfix".


record\_commit.sh
=================

Ever wondered on what you worked the past three weeks? Or you know exactly you
figured out a solution to a specific problem but can't remember in which
project it was?

Then maybe this hook can help you. It simply stores a copy of each commit
message in ` ~/.git_hooks/_data/record_commit/`. year/month subfolder are
created automatically and the file names contain the timestamp, repository and
the short commit id to make them distinct.

