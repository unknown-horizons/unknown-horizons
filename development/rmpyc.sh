#!/bin/bash
echo "Deleting all .pyc and .pyo files.."
if [ $# -gt 0 ]; then
	find "$@" -type f -name '*.pyc' -exec rm {} \; -o -name '*.pyo' -exec rm {} \;
else
	find . -type f -name '*.pyc' -exec rm {} \; -o -name '*.pyo' -exec rm {} \;
fi
echo "Done."
