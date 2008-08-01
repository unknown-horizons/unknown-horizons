#!/bin/bash
if [ $# -gt 0 ]; then
	find "$@" -type f -iname '*.pyc' -o  -iname '*.pyo' -exec rm {} \;
else
	find "$@" -type f -iname '*.pyc' -o  -iname '*.pyo' -exec rm {} \;
fi