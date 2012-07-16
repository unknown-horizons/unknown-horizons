#!/usr/bin/env python

"""
This script prints misc data from the db
in human readable form.

Run without arguments for help
"""

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
	print e.message
	print 'Please run from uh root dir'
	sys.exit(1)


from run_uh import init_environment
init_environment()

import horizons.main
from horizons.constants import UNITS, SETTLER, BUILDINGS
from horizons.scenario.actions import ACTIONS
from horizons.scenario.conditions import CONDITIONS

db = horizons.main._create_main_db()

# we also need to load entities to get access to the yaml data
from horizons.extscheduler import ExtScheduler
from horizons.component.storagecomponent import StorageComponent
from horizons.entities import Entities
from horizons.ext.dummy import Dummy
ExtScheduler.create_instance(Dummy()) # sometimes needed by entities in subsequent calls
Entities.load_buildings(db, load_now=True)
Entities.load_units(load_now=True)


def get_obj_name(obj):
	global db
	if obj < UNITS.DIFFERENCE_BUILDING_UNIT_ID:
		return db("SELECT name FROM building where id = ?", obj)[0][0]
	else:
		return db("SELECT name FROM unit where id = ?", obj)[0][0]

def get_res_name(res):
	global db
	name = db("SELECT name FROM resource WHERE id = ?", res)[0][0]
	return name

def get_settler_name(incr):
	global db
	return db("SELECT name FROM settler_level WHERE level = ?", incr)[0][0]

def get_prod_line(id, type):
	print 'Data has been moved, this view is unavailable for now'
	return
	from horizons.util.python.roman_numerals import int_to_roman
	consumption = db("SELECT resource, amount FROM production \
                      WHERE production_line = ? AND amount < 0 ORDER BY amount ASC", id)
	production = db("SELECT resource, amount FROM production \
                     WHERE production_line = ? AND amount > 0 ORDER BY amount ASC", id)
	if type is list:
		return (consumption, production)
	elif type is tuple:
		return (consumption[0], production[0])

def print_production_lines():
	print 'Data has been moved, this view is unavailable for now'
	return
	print 'Production Lines:'
	for (id, changes_anim, object, time, default) in db("SELECT id, changes_animation, object_id, time, enabled_by_default FROM production_line ORDER BY object_id"):
		(consumption,production) = get_prod_line(id, list)

		str = 'Line %2s of %2s:%-16s %5s sec %s %s ' % (id, object, get_obj_name(object), time, ('D' if default else ' '), ('C' if changes_anim else ' '))

		if consumption:
			str += 'uses: '
			for res, amount in consumption:
				str += '%2s %-16s ' % (-amount, get_res_name(res) + '(%s)' % res)

		if production:
			str += '\t=> '
			for res, amount in production:
				str +=  '%2s %-16s ' % (amount, get_res_name(res) + '(%s)' % res)

		print str

def print_verbose_lines():
	def _output_helper_prodlines(string, list):
		if len(list) == 1:
			for res, amount in list:
				print '      ' + str(string) + ':\t%s %s(%s)' % (abs(amount), get_res_name(res), res)
		elif len(list) > 1:
			print '      ' + str(string) + ': '
			for res, amount in list:
				print '\t\t%s %s (%s)' % (abs(amount), get_res_name(res), res)

	print 'Production Lines:'
	for prod_line in db("SELECT id, object_id, time, enabled_by_default FROM production_line \
	                     WHERE object_id != 3 ORDER BY object_id"):
		# do not include tent production lines here
		id = prod_line[0]
		object = prod_line[1]
		(consumption,production) = get_prod_line(id, list)

		print '%2s: %s(%s) needs %s seconds to' % (id, get_obj_name(object), object, prod_line[2])
		_output_helper_prodlines('consume', consumption)
		_output_helper_prodlines('produce', production)


def strw(s, width=0):
	"""returns string with at least width chars"""
	s = str(s)
	slen = len(s)
	diff = width - slen
	if diff > 0: s += " "*diff
	return s


def print_res():
	print 'Resources' + '\n' + '%2s: %-15s %5s %10s %19s' % ('id', 'resource', 'value', 'tradeable', 'shown_in_inventory')
	print '=' * 56
	for id, name, value, trade, inventory in db("SELECT id, name, value, tradeable, shown_in_inventory FROM resource"):
		print "%2s: %-16s %4s %6s %13s " % (id, name[0:16], value or '-', trade or '-', inventory or '-')

def print_building():
	print 'Buildings' + '\n' + 'Running costs scheme:'
	print '=' * 2 + 'Running===Paused' + '=' * 2
	for (cost, cost_inactive) in [('0-10',0),('11-24',5),('25-40',10),('>40',15)]:
		print "   %5s :   %2s" % (cost or '--', cost_inactive or '--')
	print '\n' + '=' * 23 + 'R===P' + '=' * 50
	for b in Entities.buildings.itervalues():
		print "%2s: %-16s %3s / %2s %5sx%1s %4s   %s" % \
		(b.id, b.name, b.running_costs or '--', b.running_costs_inactive or '--', \
		 b.size[0], b.size[1], b.radius, b.baseclass)

def print_unit():
	print "Units (id: name (radius) from class)"
	for u in Entities.units.itervalues():
		print "%2s: %-22s (%2s) from %s" % ((u.id - UNITS.DIFFERENCE_BUILDING_UNIT_ID),
			u.name, u.radius, u.baseclass)
	print "Add %s to each ID if you want to use them." % UNITS.DIFFERENCE_BUILDING_UNIT_ID

def print_storage():
	for b in Entities.buildings.itervalues():
		try:
			stor = b.get_component_template( StorageComponent.NAME )
		except KeyError:
			continue
		if not stor:
			continue
		inv = stor['inventory']
		try:
			inv.values()[0].values()[0]
		except IndexError:
			continue
		print '%s(%i) can store:' % (b.name, b.id)
		for res, amount in inv.values()[0].values()[0].iteritems():
			print "\t%2s tons of %s(%s)" % (amount, get_res_name(res), res)



	print "\nAll others can store 30 tons of each res:" # show buildings with default storage
	return
	all = set(db('SELECT id FROM building'))
	entries = set(db('SELECT object_id FROM storage')) # also includes units, they are ignored
	for id, in sorted(all - entries):
		print "%s(%i)" % (get_obj_name(id), id)

def print_collectors():
	print 'Collectors: (building amount collector)'
	for b, coll, amount in db("SELECT object_id, collector_class, count FROM \
			collectors ORDER BY object_id ASC"):
		print "%2s: %-18s %s %s (%s)" % (b, get_obj_name(b), amount, get_obj_name(coll), coll)

def print_building_costs():
	print 'Building costs:'
	no_costs = []
	for b in Entities.buildings.itervalues():
		if not b.costs:
			no_costs.append(b)
			continue
		s = ''
		for res, amount in b.costs.iteritems():
			s += "%4i %s(%s) " % (amount, get_res_name(res),res)
		print "%2s: %-18s %s" % (b.id, b.name, s)

	print "\nBuildings without building costs:"
	for b in no_costs:
		print "%2i: %s" % (b.id, b.name)

def print_collector_restrictions():
	for c, in db("SELECT DISTINCT collector FROM collector_restrictions"):
		print '%s(%s) is restricted to:' % (get_obj_name(c), c)
		for obj, in db("SELECT object FROM collector_restrictions WHERE collector = ?", c):
			print '\t%s(%s)' % (get_obj_name(obj),obj)

def print_increment_data():
	print 'Data has been moved, this view is unavailable for now'
	return
	from horizons.util.python.roman_numerals import int_to_roman
	upgrade_increments = xrange(1, SETTLER.CURRENT_MAX_INCR+1)
	print '%15s %s %s  %s' % ('increment', 'max_inh', 'base_tax', 'upgrade_prod_line')
	print '=' * 64
	for inc, name, inh, tax in db('SELECT level, name, inhabitants_max, tax_income FROM settler_level'):
		str = '%3s %11s %5s    %4s' % (int_to_roman(inc+1), name, inh, tax)
		if inc+1 in upgrade_increments:
			line = db("SELECT production_line FROM upgrade_material WHERE level = ?", inc+1)[0][0]
			str += 5 * ' ' + '%2s: ' % line
			(consumption, _) = get_prod_line(line, list)
			for (res, amount) in consumption:
				str += '%i %s(%s), ' % (-amount, get_res_name(res), res)
		print str

def print_colors():
	print 'Colors' + '\n' + '%2s: %12s  %3s  %3s  %3s  %3s  #%6s' % ('id', 'name', 'R ', 'G ', 'B ', 'A ', 'HEX   ')
	print '=' * 45
	for id_, name, R, G, B, alpha in db("SELECT id, name, red, green, blue, alpha FROM colors"):
		print '%2s: %12s  %3s  %3s  %3s  %3s  #' % (id_, name, R, G, B, alpha) + 3*'%02x' % (R, G, B)

def print_scenario_actions():
	print 'Available scenario actions and their arguments:'
	for action in ACTIONS.registry:
		arguments = inspect.getargspec(ACTIONS.get(action))[0][1:] # exclude session
		print '%-12s  %s' % (action, arguments or '')

def print_scenario_conditions():
	print 'Available scenario conditions and their arguments:'
	for condition in CONDITIONS.registry:
		arguments = inspect.getargspec(CONDITIONS.get(condition))[0][1:] # exclude session
		print '%-36s  %s' % (condition, arguments or '')

def print_names():
	text = ''
	for (table, type) in [('city', 'player'), ('city', 'pirate'), ('ship','player'), ('ship','pirate'), ('ship','fisher'), ('ship','trader')]:
		sql = "SELECT name FROM %snames WHERE for_%s = 1" % (table, type)
		names = db(sql)
		text += '\n' + "%s %s names" % (type, table) + '[list]\n'
		for name in map(lambda x: x[0], names):
			text += '[*] %s' % name + '\n'
		text += '[/list]' + '\n'
	print text

def print_settler_needs():
	klass = Entities.buildings[ BUILDINGS.RESIDENTIAL ]
	comp = [ i for i in klass.component_templates if i.keys()[0] == u'ProducerComponent' ][0]
	lines = comp.values()[0][u'productionlines']
	per_level = defaultdict(list)
	for line_data in lines.itervalues():
		level = line_data.get("level", [-1])
		for l in level:
			per_level[l].extend( [ res for (res, num) in line_data[u'consumes'] ] )
	data = dict( (k, sorted(db.get_res_name(i) for i in v)) for k,v in per_level.iteritems())
	print "Needed resources per increment"
	pprint.pprint(data)
	print '\nChanges per level:'
	for i in xrange(len(data)-2):
		s = str(i)+"/"+str(i+1)+": "
		for r in data[i+1]:
			if r not in data[i]:
				s += "+"+r+", "
		for r in data[i]:
			if r not in data[i+1]:
				s += "-"+r+", "
		print s


functions = {
		'actions' : print_scenario_actions,
		'buildings' : print_building,
		'building_costs' : print_building_costs,
		'colors' : print_colors,
		'collectors' : print_collectors,
		'collector_restrictions': print_collector_restrictions,
		'conditions' : print_scenario_conditions,
		'increments' : print_increment_data,
		'lines' : print_production_lines,
		'names' : print_names,
		'resources' : print_res,
    'settler_needs' : print_settler_needs,
		'storage' : print_storage,
		'units' : print_unit,
		'verbose_lines' : print_verbose_lines,
		}
abbrevs = {
		'b' : 'buildings',
		'bc': 'building_costs',
		'building' : 'buildings',
		'c' : 'collectors',
		'cl' : 'colors',
		'cr': 'collector_restrictions',
		'i' : 'increments',
		'increment' : 'increments',
		'n' : 'names',
		'res' : 'resources',
		'settler_lines': 'increments',
		'sl': 'increments',
		'sn': 'settler_needs',
		'unit': 'units',
		'vl': 'verbose_lines',
		}

flags = dict(functions)
for (x,y) in abbrevs.iteritems(): # add convenience abbreviations to possible flags
	flags[x] = functions[y]

args = sys.argv

print 'WARNING: most of the features are currently broken since units and buildings are now represented differently.'

if len(args) == 1:
	print 'Start with one of those args: %s \nSupported abbreviations: %s' % (sorted(functions.keys()), sorted(abbrevs.keys()))
else:
	for i in flags.iteritems():
		if i[0].startswith(args[1]):
			i[1]()
			sys.exit(0)
	print 'Start with one of those args: %s \nSupported abbreviations: %s' % (functions.keys(), abbrevs.keys())
