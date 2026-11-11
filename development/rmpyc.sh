#!/bin/bash
echo "Deleting all .pyc and .pyo files.."
if [ $# -gt 0 ]; then
	targets=("$@")
else
	targets=(.)
fi
find "${targets[@]}" -type f \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -f {} +
echo "Done."
