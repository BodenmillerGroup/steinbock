#!/usr/bin/env bash
eval $( fixuid -q )
python -m steinbock "$@"
