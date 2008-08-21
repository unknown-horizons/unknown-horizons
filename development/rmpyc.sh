#!/bin/bash
if [ $# -gt 0 ]; then
	find "$@" -type f -name '*.pyc' -o -name '*.pyo' -exec rm {} \;
else
	find . -type f -name '*.pyc' -o -name '*.pyo' -exec rm {} \;
fi
