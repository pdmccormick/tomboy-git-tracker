#!/usr/bin/env python

import posix, re

class DiffMunger:
    START_REV=6
    END_REV=1569
    REPO="/home/pete/scratchcode/tomboy-hg2git/tomboy"

    tag_extract = re.compile("^<([^>]*)>")

    def __init__(self):
        self.lines = None
        self.changes = None
        
    def get_patch(self, start, end):
        cmd = "hg -R %s diff -r %d -r %d" % (DiffMunger.REPO, start, end)
        p = posix.popen(cmd)
        self.lines = [ k.strip() for k in p.readlines() ]
        p.close()

    def parse_patch(self, rev):
        self.get_patch(rev, rev + 1)

        self.changes = { }
        key = ""
        changes = []
        ignoring = True
        
        for line in self.lines:
            if line.startswith("diff "):
                key = line.split(" ")[-1]
                ignoring = True

                if key.endswith(".note"):
                    ignoring = False
                    self.changes[key] = []

                continue

            if ignoring or line.startswith("+++ ") or line.startswith("--- "):
                continue

            if line.startswith("+") or line.startswith("-"):
                line = line[1:].strip()
                self.changes[key].append(line)

                #m = DiffMunger.tag_extract.match(line)
                #if m: tag = m.group(1)


if __name__ == '__main__':
    dm = DiffMunger()

    dm.parse_patch(1566)

    print dm.changes

