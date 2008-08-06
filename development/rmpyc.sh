#!/bin/bash
if [ $# -gt 0 ]; then
	find "$@" -type f -iname '*.pyc' -exec rm {} \;
	find "$@" -type f -iname '*.pyo' -exec rm {} \;
else
	find . -type f -iname '*.pyc' -exec rm {} \;
	find . -type f -iname '*.pyo' -exec rm {} \;
fi

