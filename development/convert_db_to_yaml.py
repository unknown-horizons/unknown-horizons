#!/usr/bin/env python2

"""
This script prints misc data from the db
in human readable form.

Run without arguments for help
"""

import os.path
import sys
from collections import OrderedDict
import collections
from yaml import load, dump
import yaml
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

sys.path.append(".")
sys.path.append("./horizons")
sys.path.append("./horizons/util")

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

db = horizons.main._create_main_db()


def construct_ordered_mapping(self, node, deep=False):
	if not isinstance(node, yaml.MappingNode):
		raise ConstructorError(None, None,
				               "expected a mapping node, but found %s" % node.id,
				               node.start_mark)
	mapping = collections.OrderedDict()
	for key_node, value_node in node.value:
		key = self.construct_object(key_node, deep=deep)
		if not isinstance(key, collections.Hashable):
			raise ConstructorError("while constructing a mapping", node.start_mark,
						           "found unhashable key", key_node.start_mark)
		value = self.construct_object(value_node, deep=deep)
		mapping[key] = value
	return mapping

yaml.constructor.BaseConstructor.construct_mapping = construct_ordered_mapping


def construct_yaml_map_with_ordered_dict(self, node):
	data = collections.OrderedDict()
	yield data
	value = self.construct_mapping(node)
	data.update(value)

yaml.constructor.Constructor.add_constructor(
    'tag:yaml.org,2002:map',
    construct_yaml_map_with_ordered_dict)


def represent_ordered_mapping(self, tag, mapping, flow_style=None):
	value = []
	node = yaml.MappingNode(tag, value, flow_style=flow_style)
	if self.alias_key is not None:
		self.represented_objects[self.alias_key] = node
	best_style = True
	if hasattr(mapping, 'items'):
		mapping = list(mapping.items())
	for item_key, item_value in mapping:
		node_key = self.represent_data(item_key)
		node_value = self.represent_data(item_value)
		if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
			best_style = False
		if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
			best_style = False
		value.append((node_key, node_value))
	if flow_style is None:
		if self.default_flow_style is not None:
			node.flow_style = self.default_flow_style
		else:
			node.flow_style = best_style
	return node

yaml.representer.BaseRepresenter.represent_mapping = represent_ordered_mapping

yaml.representer.Representer.add_representer(collections.OrderedDict,
                                             yaml.representer.SafeRepresenter.represent_dict)

def get_prod_line(id):
	consumption = db("SELECT resource, amount FROM production \
                      WHERE production_line = ? AND amount < 0 ORDER BY amount ASC", id)
	production = db("SELECT resource, amount FROM production \
                     WHERE production_line = ? AND amount > 0 ORDER BY amount ASC", id)
	return (list([list(x) for x in consumption]), list([list(x) for x in production]))

result = OrderedDict()

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

	costs =  {}
	for (name, value) in db("SELECT resource, amount FROM building_costs WHERE building = ?", id):
		costs[name]=value

	result['buildingcosts'] =  costs

	result['components'] = []

	result['components'].append({'HealthComponent': {'maxhealth': health}})

	production_lines = {}
	for num, (prodlineid, changes_anim, object, time, default) in enumerate(db("SELECT id, changes_animation, object_id, time, enabled_by_default FROM production_line WHERE object_id=?", id)):
		(consumption,production) = get_prod_line(prodlineid)
		prod_line =  { 'time': int(time) }
		if changes_anim == 0:
			prod_line['changes_animation'] = False
		if default == 0:
			prod_line['enabled_by_default'] = False
		if production:
			prod_line['produces'] = production
		if consumption:
			prod_line['consumes'] = consumption

		level = db("SELECT level from settler_production_line WHERE production_line=?", prodlineid)
		if level:
			prod_line['level'] = [ x for (x,) in level]

		production_lines[prodlineid] = prod_line

	if production_lines:
		result['components'].append({'ProducerComponent': {'productionlines': production_lines}})

	query_result = db("SELECT resource, size FROM storage WHERE object_id=?", id)
	if not query_result:
		result['components'].append('StorageComponent')
	else:
		slot_sizes = {}
		for resource, size in query_result:
			slot_sizes[resource] = size
		result['components'].append({'StorageComponent': {'inventory': {'SlotsStorage': {'slot_sizes': slot_sizes}}}})

	result['actionsets'] =  {}

	for action_set, preview_set, level in  db("SELECT action_set_id, preview_action_set_id, level FROM action_set WHERE object_id=?", id):
		result['actionsets'][action_set] =  {'level': level}
		if preview_set is not None:
			result['actionsets'][action_set]['preview'] = preview_set



	soundfiles = list(db("SELECT file FROM sounds INNER JOIN object_sounds ON sounds.rowid = object_sounds.sound AND object_sounds.object = ?", id))
	if len(soundfiles) >  0:
		result['components'].append({'AmbientSoundComponent': {'soundfiles':  [x[0] for x in soundfiles]}})

	filename = str(result['name']).lower().strip().replace(" ",  "").replace("'", "") + ".yaml"
	stream = file("content/objects/buildings/" + filename, 'w')
	dump(result, stream=stream)



