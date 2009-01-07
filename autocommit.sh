#!/bin/sh

# autocommit.sh -- once more, with feeling

BASE="$HOME/.tomboy"
MSG="autocommit.sh: $(date)"

cd $BASE
./filter-scm.py | sh -e
git commit -m "$MSG"

