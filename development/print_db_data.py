#!/usr/bin/env python3

# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

"""
This script prints misc data from the db
in human readable form.

Run without arguments for help
"""
from __future__ import print_function

import inspect
import pprint
import sys
from collections import defaultdict

sys.path.append(".")
sys.path.append("./horizons")
sys.path.append("./horizons/util")

try:
	import run_uh
except ImportError as e:
	print(e.message)
	print('Please run from uh root dir')
	sys.exit(1)


from run_uh import init_environment
init_environment(True)

import horizons.main
from horizons.constants import UNITS, BUILDINGS, TIER
from horizons.scenario.actions import ACTIONS
from horizons.scenario.conditions import CONDITIONS

db = horizons.main._create_main_db()

# we also need to load entities to get access to the yaml data
from horizons.extscheduler import ExtScheduler
from horizons.component.storagecomponent import StorageComponent
from horizons.entities import Entities
from tests.dummy import Dummy
ExtScheduler.create_instance(Dummy()) # sometimes needed by entities in subsequent calls
Entities.load_buildings(db, load_now=True)
Entities.load_units(load_now=True)

building_name_mapping = dict((b.id, b.name) for b in Entities.buildings.itervalues())
unit_name_mapping = dict((u.id, u.name) for u in Entities.units.itervalues())


def get_obj_name(obj):
	global db
	if obj < UNITS.DIFFERENCE_BUILDING_UNIT_ID:
		return db("SELECT name FROM building where id = ?", obj)[0][0]
	else:
		return unit_name_mapping[obj]


def get_res_name(res):
	global db
	try:
		name = db("SELECT name FROM resource WHERE id = ?", res)[0][0]
	except IndexError: # might be a unit instead
		name = get_obj_name(res)
	return name


def get_settler_name(tier):
	global db
	return db("SELECT name FROM tier WHERE level = ?", tier)[0][0]


def format_prodline(line_list, depth):
	for res, amount in line_list:
		print(' ' * depth, '{amount:>4} {name:16} ({id:2})'.format(
			amount=abs(amount), name=get_res_name(res), id=res))


def print_production_lines():
	print('Production lines per building:')
	for b in Entities.buildings.itervalues():
		print('\n', b.name, '\n', '=' * len(b.name))
		for comp in b.component_templates:
			if not isinstance(comp, dict):
				continue
			for name, data in comp.iteritems():
				if 'produce' not in name.lower():
					continue
				for id, dct in data.get('productionlines').iteritems():
					if not dct:
						continue
					changes_animation = dct.get('changes_animation') is None
					changes_anim_text = changes_animation and 'changes animation' or 'does not change animation'
					disabled_by_default = dct.get('enabled_by_default') is not None
					enabled_text = (disabled_by_default and 'not ' or '') + 'enabled by default'
					time = dct.get('time') or 1
					print('{time:>3}s'.format(time=time), '(' + changes_anim_text + ',', enabled_text + ')')
					consumes = dct.get('consumes')
					if consumes:
						print('   consumes')
						format_prodline(consumes, 4)
					produces = dct.get('produces')
					if produces:
						print('   produces')
						format_prodline(produces, 4)


def print_verbose_lines():
	print('Data has been moved, this view is unavailable for now')
	return

	def _output_helper_prodlines(string, list):
			if len(list) == 1:
					for res, amount in list:
							print('	  ' + str(string) + ':\t%s %s(%s)' % (abs(amount), get_res_name(res), res))
			elif len(list) > 1:
					print('	  ' + str(string) + ': ')
					for res, amount in list:
							print('\t\t%s %s (%s)' % (abs(amount), get_res_name(res), res))

	print('Production Lines:')
	for prod_line in db("SELECT id, object_id, time, enabled_by_default FROM production_line \
	                     WHERE object_id != 3 ORDER BY object_id"):
			# do not include tent production lines here
			id = prod_line[0]
			object = prod_line[1]
			(consumption, production) = get_prod_line(id, list)

			print('%2s: %s(%s) needs %s seconds to' % (id, get_obj_name(object), object, prod_line[2]))
			_output_helper_prodlines('consume', consumption)
			_output_helper_prodlines('produce', production)


def print_res():
	print('Resources\n{:2s}: {:-15s} {:5s} {:10s} {19s}'
	      .format('id', 'resource', 'value', 'tradeable', 'shown_in_inventory'))
	print('=' * 56)
	for id, name, value, trade, inventory in db("SELECT id, name, value, tradeable, shown_in_inventory FROM resource"):
		print("{:2s}: {:-16s} {:4s} {:6s} {:13s} "
		      .format(id, name[0:16], value or '-', trade or '-', inventory or '-'))


def print_building():
	print('Buildings\nRunning costs scheme:')
	print('=' * 2 + 'Running===Paused' + '=' * 2)
	for (cost, cost_inactive) in [('0-10', 0), ('11-24', 5), ('25-40', 10), ('>40', 15)]:
		print("   {:5s} :   {:2s}".format(cost or '--', cost_inactive or '--'))
	print('\n' + '=' * 23 + 'R===P' + '=' * 50)
	for b in Entities.buildings.itervalues():
		print("{:2s}: {:-16s} {:3s} / {:2s} {:5s}x{:1s} {:4s}   {}"
		      .format(b.id, b.name, b.running_costs or '--',
		              b.running_costs_inactive or '--', b.size[0], b.size[1],
		              b.radius, b.baseclass))


def print_unit():
	print("Units (id: name (radius) from class)")
	for u in Entities.units.itervalues():
		print("{:2s}: {:-22s} ({:2s}) from {}"
		      .format((u.id - UNITS.DIFFERENCE_BUILDING_UNIT_ID),
		              u.name, u.radius, u.baseclass))
	print("Add {} to each ID if you want to use them."
	      .format(UNITS.DIFFERENCE_BUILDING_UNIT_ID))


def print_storage():
	for b in Entities.buildings.itervalues():
		try:
			stor = b.get_component_template(StorageComponent)
		except KeyError:
			continue
		if not stor:
			continue
		try:
			stor.values()[0].values()[0]
		except IndexError:
			continue
		print('{}({:i}) can store:'.format(b.name, b.id))
		for res, amount in stor.values()[0].values()[0].iteritems():
			print("\t{:2s} tons of {}({})".format(amount, get_res_name(res), res))

	print("\nAll others can store 30 tons of each res.")
	#TODO show buildings with default storage here


def print_collectors():
	print('Collectors: (building amount collector)')
	for b in Entities.buildings.itervalues():
		for comp in b.component_templates:
			if not isinstance(comp, dict):
				continue
			for name, data in comp.iteritems():
				if 'collect' not in name.lower():
					continue
				for id, amount in data.get('collectors').iteritems():
					print("{:2s}: {:-18s} {} {} ({})"
					      .format(b.id, b.name, amount, get_obj_name(id), id))


def print_building_costs():
	print('Building costs:')
	no_costs = []
	for b in Entities.buildings.itervalues():
		if not b.costs:
			no_costs.append(b)
			continue
		s = ''
		for res, amount in b.costs.iteritems():
			s += "{:4i} {}({}) ".format(amount, get_res_name(res), res)
		print("{:2s}: {-18s} {s}".format(b.id, b.name, s))

	print("\nBuildings without building costs:")
	for b in no_costs:
		print("{2i}: {}".format(b.id, b.name))


def print_collector_restrictions():
	for u in Entities.units.itervalues():
		for comp in u.component_templates:
			if not isinstance(comp, dict):
				continue
			for name, data in comp.iteritems():
				if 'restricted' not in name.lower():
					continue
				print('{}({}) is restricted to:'.format(u.class_name, u.id))
				for building in data.get('allowed'):
					print('\t{}({})'.format(building_name_mapping[building], building))


def print_tier_data():
	print('Data has been moved, this view is unavailable for now')
	return
	upgrade_tiers = xrange(1, TIER.CURRENT_MAX + 1)
	print('{:15s} {} {}  {}'.format('tier', 'max_inh', 'base_tax', 'upgrade_prod_line'))
	print('=' * 64)
	for inc, name, inh, tax in db('SELECT level, name, inhabitants_max, tax_income FROM tier'):
		str = '{:3s} {:11s} {:5s}    {:4s}'.format((inc + 1), name, inh, tax)
		if inc + 1 in upgrade_tiers:
			line = db("SELECT production_line FROM upgrade_material WHERE level = ?", inc + 1)[0][0]
			str += 5 * ' ' + '{:2s}: '.format(line)
			(consumption, _) = get_prod_line(line, list)
			for (res, amount) in consumption:
				str += '{i[ {}({}), '.format(-amount, get_res_name(res), res)
		print(str)


def print_colors():
	print('Colors\n{:2s}: {:12s}  {:3s}  {:3s}  {:3s}  {:3s}  #{:6s}'
	      .format('id', 'name', 'R ', 'G ', 'B ', 'A ', 'HEX   '))
	print('=' * 45)
	for id_, name, R, G, B, alpha in db("SELECT id, name, red, green, blue, alpha FROM colors"):
		print('{:2s}: {:12s}  {:3s}  {:3s}  {:3s}  {:3s}  #'
		      .format(id_, name, R, G, B, alpha) + 3 * '{:02x}'.format(R, G, B))


def print_scenario_actions():
	print('Available scenario actions and their arguments:')
	for action in ACTIONS.registry:
		arguments = inspect.getargspec(ACTIONS.get(action))[0][1:] # exclude session
		print('{:-12s}  {}'.format(action, arguments or ''))


def print_scenario_conditions():
	print('Available scenario conditions and their arguments:')
	for condition in CONDITIONS.registry:
		arguments = inspect.getargspec(CONDITIONS.get(condition))[0][1:] # exclude session
		print('{:-36s}  {}'.format(condition, arguments or ''))


def print_names():
	text = ''
	for (table, type) in [
			('city', 'player'), ('city', 'pirate'), ('ship', 'player'),
			('ship', 'pirate'), ('ship', 'fisher'), ('ship', 'trader')]:
		sql = "SELECT name FROM {}names WHERE for_{} = 1".format(table, type)
		names = db(sql)
		text += '\n' + "{} {} names[list]\n".format(type, table)
		for name in map(lambda x: x[0], names):
			text += '[*] {}\n'.format(name)
		text += '[/list]' + '\n'
	print(text)


def print_settler_needs():
	klass = Entities.buildings[BUILDINGS.RESIDENTIAL]
	comp = [i for i in klass.component_templates if i.keys()[0] == u'ProducerComponent'][0]
	lines = comp.values()[0][u'productionlines']
	per_level = defaultdict(list)
	for line_data in lines.itervalues():
		level = line_data.get("level", [-1])
		for l in level:
			per_level[l].extend([res for (res, num) in line_data[u'consumes']])
	data = dict((k, sorted(db.get_res_name(i) for i in v)) for k, v in per_level.iteritems())
	print("Needed resources per tier")
	pprint.pprint(data)
	print('\nChanges per level:')
	for i in xrange(len(data) - 2):
		s = str(i) + "/" + str(i + 1) + ": "
		for r in data[i + 1]:
			if r not in data[i]:
				s += "+" + r + ", "
		for r in data[i]:
			if r not in data[i + 1]:
				s += "-" + r + ", "
		print(s)


functions = {
	'actions': print_scenario_actions,
	'buildings': print_building,
	'building_costs': print_building_costs,
	'colors': print_colors,
	'collectors': print_collectors,
	'collector_restrictions': print_collector_restrictions,
	'conditions': print_scenario_conditions,
	'tiers': print_tier_data,
	'lines': print_production_lines,
	'names': print_names,
	'resources': print_res,
	'settler_needs': print_settler_needs,
	'storage': print_storage,
	'units': print_unit,
	'verbose_lines': print_production_lines,
}
abbrevs = {
	'b': 'buildings',
	'bc': 'building_costs',
	'building': 'buildings',
	'c': 'collectors',
	'cl': 'colors',
	'cr': 'collector_restrictions',
	'i': 'tiers',
	'tier': 'tiers',
	'n': 'names',
	'pl': 'lines',
	'res': 'resources',
	'settler_lines': 'tiers',
	'sl': 'tiers',
	'sn': 'settler_needs',
	'unit': 'units',
	'vl': 'verbose_lines',
}

flags = dict(functions)
for (x, y) in abbrevs.iteritems(): # add convenience abbreviations to possible flags
	flags[x] = functions[y]

args = sys.argv

if len(args) == 1:
	print('Start with one of those args: {} \nSupported abbreviations: {}'
	      .format(sorted(functions.keys()), sorted(abbrevs.keys())))
else:
	for i in flags.iteritems():
		if i[0].startswith(args[1]):
			i[1]()
			sys.exit(0)
	print('Start with one of those args: {} \nSupported abbreviations: {}'
	      .format(functions.keys(), abbrevs.keys()))
