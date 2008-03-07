#!/bin/bash

# Change to your FIFE checkout dir
fife_dir="../../fife-trunk"

echo "Trying to start OA with FIFE in '$fife_dir'"

export PYTHONPATH="$fife_dir/engine/swigwrappers/python:$fife_dir/engine/extensions"
export LD_LIBRARY_PATH="$fife_dir/ext/minizip:$fife_dir/ext/install/lib"

$DBG python ./openanno.py
