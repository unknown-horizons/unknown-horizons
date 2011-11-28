#!/usr/bin/env python2

"""
This script prints misc data from the db
in human readable form.

Run without arguments for help
"""

import os.path
import sys
from collections import OrderedDict
from yaml import load, dump
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

sys.path.append(".")
sys.path.append("./horizons")
sys.path.append("./horizons/util")

import gettext
gettext.install('', unicode=True)

try:
	import run_uh
except ImportError as e:
	print e.message
	print 'Please run from uh root dir'
	sys.exit(1)


from run_uh import init_environment
init_environment()

import horizons.main
from horizons.constants import UNITS, SETTLER

db = horizons.main._create_db()

def get_prod_line(id):
	consumption = db("SELECT resource, amount FROM production \
                      WHERE production_line = ? AND amount < 0 ORDER BY amount ASC", id)
	production = db("SELECT resource, amount FROM production \
                     WHERE production_line = ? AND amount > 0 ORDER BY amount ASC", id)
	return (list([list(x) for x in consumption]), list([list(x) for x in production]))

result = dict()

for id, name, c_type, c_package, x, y, radius, cost, cost_inactive, inhabitants_start, inhabitants_max, button_name, tooltip_text, health, settler_level in \
    db('SELECT id, name, class_type, class_package, size_x, size_y, radius, cost_active, cost_inactive, inhabitants_start, inhabitants_max, button_name, tooltip_text, health, settler_level FROM \
		building LEFT OUTER JOIN building_running_costs ON building_running_costs.building = building.id\
		ORDER BY id'):

	result['id'] = id
	result['name'] = name
	result['baseclass'] = c_package + "." + c_type
	result['radius'] = radius
	result['cost'] = cost if cost is not None else 0
	result['cost_inactive'] = cost_inactive if cost_inactive is not None else 0
	result['size_x'] = x
	result['size_y'] = y
	result['inhabitants_start'] = inhabitants_start
	result['inhabitants_max'] = inhabitants_max
	result['button_name'] = button_name
	result['tooltip_text'] = tooltip_text
	result['settler_level'] = settler_level

	result['components'] = {}

	result['components']['HealthComponent'] = {'maxhealth': health}

	production_lines = {}
	for num, (prodlineid, changes_anim, object, time, default) in enumerate(db("SELECT id, changes_animation, object_id, time, enabled_by_default FROM production_line WHERE object_id=?", id)):
		(consumption,production) = get_prod_line(prodlineid)
		prod_line =  { 'time': int(time) }
		if changes_anim == 0:
			prod_line['changes_animation'] = False
		if default == 0:
			prod_line['enabled_by_default'] = False
		if len(production) > 0:
			prod_line['produces'] = production
		if len(consumption) > 0:
			prod_line['consumes'] = consumption

		production_lines[num] = prod_line

	if len(production_lines) > 0:
		result['components']['ProducerComponent'] =  {'productionlines': production_lines}

	result['actionsets'] =  {}

	for action_set, preview_set, level in  db("SELECT action_set_id, preview_action_set_id, level FROM action_set WHERE object_id=?", id):
		result['actionsets'][action_set] =  {'level': level}
		if preview_set is not None:
			result['actionsets'][action_set]['preview'] = preview_set



	filename = str(result['name']).lower().strip().replace(" ",  "").replace("'", "") + ".yaml"
	stream = file("content/objects/buildings/" + filename, 'w')
	dump(result, stream=stream, Dumper=Dumper)




