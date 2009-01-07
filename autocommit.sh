#!/bin/sh

# autocommit.sh -- once more, with feeling

BASE="$HOME/.tomboy"
MSG="autocommit.sh: $(date)"

cd $BASE
./git-tomboy-tracker.py | sh -e
git commit -m "$MSG"

