#!/usr/bin/env python

import posix, re, sys
from itertools import *

def git(cmd):
    return run_output("git " + cmd)

def run_output(cmd):
    p = posix.popen(cmd)
    lines = [ l.rstrip() for l in p.readlines() ]
    p.close()
    return lines

class GitRepo:
    def __init__(self, path):
        self.path = path
        self.revs = dict()
        self.base_revs = []

    def git(self, cmd):
        return git("--git-dir=%s %s" % (self.path, cmd))

    def load_revs(self):
        for line in self.git("rev-list --all --parents"):
            ps = line.split(" ")

            if len(ps) == 2:
                (rev, parent) = ps
                self.revs[rev] = parent
            else:
                self.base_revs.append(ps[0])

    def diff(self, start='', end=''):
        return self.git("diff %s %s" % (start, end))

    def find_child(self, parent):
        return [ rev for (rev, parent_) in self.revs.items() if parent_ == parent ]

    def chain(self, start):
        last = start

        while True:
            child = self.find_child(last)
            
            if len(child) == 0:
                return

            assert len(child) == 1, "Can't handle branching history at rev %s" % last
            (child, ) = child

            yield child
            last = child

    def updated(self, extra=''):
        code_map = { 'C': 'changed', 'R': 'removed', '?': 'unknown' }

        pairs = [ k.split(' ') for k in self.git("ls-files -d -m -t -o %s" % extra) ]
        ups = { 'changed': [], 'removed': [], 'unknown': [] }
        for (u, v) in pairs:
            if u not in code_map:
                continue

            u = code_map[u]
            ups[u].append(v)

        return ups


class DiffMunger:
    tag_extract = re.compile("^<([^>]*)>")
    metadata_tags = [ 'last-change-date', 'last-metadata-change-date', 'cursor-position', 'width', 'height', 'x', 'y', 'open-on-startup' ]

    def __init__(self):
        self.changes = dict()

    def parse_diff(self, lines):
        self.changes = {}
        key = ""
        changes = []
        ignoring = True

        line_num = 0
        for line in lines:
            line_num += 1

            # Look for start of a file diff block
            if line.startswith("diff "):
                key = line.split(" ")[-1].split('/')[-1]
                ignoring = False
                self.changes[key] = []
                continue

            # Ignore the non-change lines
            if ignoring or line.startswith("+++ ") or line.startswith("--- ") or line.startswith('index ') or line.startswith('@@ '):
                continue

            # Consider only deletions and removals
            if line.startswith("+") or line.startswith("-"):
                line = line[1:].strip()
                self.changes[key].append((line_num, line))

                # Look for a tag at the start of the line
                m = DiffMunger.tag_extract.match(line)
                real = False

                if m:
                    tag = m.group(1)

                    # If it's a metadata tag, we don't care
                    if tag not in DiffMunger.metadata_tags:
                        real = True
                else:
                    real = True

                # If this represents a real change...
                if real:
                    yield key
                    ignoring = True

def trawl_history(repo):
    root = repo.base_revs[0]
    chain = repo.chain(root)

    dm = DiffMunger()

    parent = root
    for child in chain:
        diff = repo.diff(parent, child)
        dm.parse_diff(diff)

        for (k,v) in dm.changes.items():
            print k, ':'
            for line in v:
                print "\t", line
        
        return

        parent = child


if __name__ == '__main__':
    repo_path = '.git'
    repo = GitRepo(repo_path)

#    repo.load_revs()
#    trawl_history(repo)

    diff = repo.diff()
    dm = DiffMunger()

    excluded = [ 'autocommit.sh', 'git-tomboy-tracker.py' ]
    included = [ 'manifest.xml' ]

    updates = repo.updated()

    removed = [ r for r in updates['removed'] if r in included or r not in excluded ]
    excluded.extend(removed)
    changed = [ c for c in dm.parse_diff(diff) if c in included or c not in excluded ]
    newfiles = [ n for n in updates['unknown'] if n.endswith('.note') and '/' not in n ]
    changed.extend(newfiles)

    # Non-trivial file changes
    for k in changed:
        print 'git add ' + k

    for k in removed:
        print 'git rm -q ' + k

