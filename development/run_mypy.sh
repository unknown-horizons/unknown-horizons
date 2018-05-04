#!/bin/bash

# Wrapper around mypy to ignore files that have issues with mypy

if [ $# -gt 0 ]; then
	args=$@
else
	args=horizons
fi

# These files produce errors we can't silence/fix for now
#
#   https://github.com/python/mypy/issues/2377
#   https://github.com/python/mypy/issues/1237

mypy $args | grep -v -e horizons/world/building/storages.py \
                     -e horizons/world/building/path.py \
                     -e horizons/world/building/unitproduction.py \
                     -e horizons/world/building/war.py \
                     -e horizons/world/units/groundunit.py \
                     -e horizons/world/building/settler.py \
                     -e horizons/world/units/animal.py \
                     -e horizons/world/units/fightingship.py \
                     -e horizons/world/units/ship.py \
                     -e horizons/world/building/production.py \
                     -e horizons/world/building/nature.py \
                     -e horizons/gui/widgets/productionoverview.py
