#!/usr/bin/env bash
test ${RUN_FIXUID} && eval $( fixuid -q )
python -m steinbock "$@"
