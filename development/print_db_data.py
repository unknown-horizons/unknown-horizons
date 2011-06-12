#!/usr/bin/env python

"""
This script prints misc data from the db
in human readable form.

Run without arguments for help
"""

import os.path
import sys

dbfile = 'content/game.sqlite'

if not os.path.exists(dbfile):
	print 'please run from uh root dir'
	sys.exit(1)

sys.path.append(".")
sys.path.append("./horizons")
sys.path.append("./horizons/util")

import gettext
gettext.install('', unicode=True)

from run_uh import init_environment
init_environment()

import horizons.main
from horizons.constants import UNITS, SETTLER

db = horizons.main._create_db()

def get_obj_name(obj):
	global db
	if obj < UNITS.DIFFERENCE_BUILDING_UNIT_ID:
		return db("SELECT name FROM building where id = ?", obj)[0][0]
	else:
		return db("SELECT name FROM unit where id = ?", obj)[0][0]

def get_res_name(res):
	global db
	return db("SELECT name FROM resource WHERE id = ?", res)[0][0]

def get_settler_name(incr):
	global db
	return db("SELECT name FROM settler.settler_level WHERE level = ?", incr)[0][0]

def get_prod_line(id, type):
	consumption = db("SELECT resource, amount FROM balance.production \
                      WHERE production_line = ? AND amount < 0 ORDER BY amount ASC", id)
	production = db("SELECT resource, amount FROM balance.production \
                     WHERE production_line = ? AND amount > 0 ORDER BY amount ASC", id)
	if type is list:
		return (consumption, production)
	elif type is tuple:
		return (consumption[0], production[0])

def print_production_lines():
	print 'Production Lines:'
	for (id, object, time, default) in db("SELECT id, object_id, time, enabled_by_default FROM production_line ORDER BY object_id"):
		(consumption,production) = get_prod_line(id, list)

		str = 'ProdLine %2s of %2s:%-16s %5s sec %s\t' % (id, object, get_obj_name(object), time, ('D' if default else ' '))

		if len(consumption) > 0:
			str += 'consumes: '
			for res, amount in consumption:
				str += '%s %s(%s), ' % (-amount, get_res_name(res), res)

		if len(production) > 0:
			str += '\tproduces: '
			for res, amount in production:
				str +=  '%s %s(%s), ' % (amount, get_res_name(res), res)

		print str

def print_settler_lines():
	print 'Settler Consumption Lines:'
	for incr in xrange(0,SETTLER.CURRENT_MAX_INCR + 1):
		settlername = get_settler_name(incr)
		print "Inhabitants of increment %i (%ss) desire the following goods:" % \
		                               (incr, settlername)
		lines = db("SELECT production_line FROM settler.settler_production_line \
		            WHERE level = ? ORDER BY production_line", incr)
		sorted_lines = sorted([(get_prod_line(line[0], tuple)[0][0],line[0]) for i,line in enumerate(lines)])
		for item,id in sorted_lines:
			time = db("SELECT time FROM production_line WHERE id == ?",id)[0][0]
			str = '%2s: Each %5s seconds, %ss consume ' % (id, time, settlername)
			(consumption,production) = get_prod_line(id, tuple)
			str += '%2i %-12s(%2s) for ' % (-consumption[1], get_res_name(consumption[0]), consumption[0])
			str += '%2i %s(%2s).' % (production[1], get_res_name(production[0]), production[0])
			print str
		print ''

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
	print "Resources (id: resource (value))"
	for id, name, value in db("SELECT id, name, value FROM resource"):
		print "%2s:  %s (%s)" % (id, name, value or 0)

def print_building():
	print "Buildings (id: name running_costs, size, radius, from class):"
	for id, name, c_type, c_package, x, y, radius, cost, cost_inactive in \
			db('SELECT id, name, class_type, class_package, size_x, size_y, radius, cost_active, cost_inactive FROM \
			building LEFT OUTER JOIN balance.building_running_costs ON balance.building_running_costs.building = building.id'):
		cost = " 0" if cost is None else cost
		print "%2s: %-16s %2s$/%2s$  %sx%s  %-2s  from %s.%s" % (id, name, cost, cost_inactive or 0, x, y, radius, c_package, c_type)

def print_unit():
	print "Units (id: name from class)"
	for id, name, c_type, c_package in db("SELECT id, name, class_type, class_package FROM unit"):
		print "%2s: %-22s from %s.%s" % ((id - UNITS.DIFFERENCE_BUILDING_UNIT_ID), name, c_package, c_type)
	print "Add %s to each ID if you want to use them." % UNITS.DIFFERENCE_BUILDING_UNIT_ID

def print_storage():
	for (obj, ) in db('SELECT DISTINCT object_id FROM storage'):
		print '%s(%i) can store:' % (get_obj_name(obj), obj)
		for res, amount in db("SELECT resource, size FROM storage WHERE object_id = ?", obj):
			print "\t%2s tons of %s(%s)" % (amount, get_res_name(res), res)

	print "\nAll others can store 30 tons of each res:" # show buildings with default storage
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
	for b, in db("SELECT DISTINCT building FROM balance.building_costs"):
		s = ''
		for res, amount in db("SELECT resource, amount FROM balance.building_costs WHERE building = ?", b):
			s += "%4i %s(%s) " % (amount, get_res_name(res),res)
		print "%2s: %-18s %s" % (b, get_obj_name(b), s)

	print "\nBuildings without building costs:"
	all = set(db('SELECT id FROM building'))
	entries = set(db('SELECT DISTINCT building FROM balance.building_costs'))
	for id, in sorted(all - entries):
		print "%s(%i)" % (get_obj_name(id), id)

def print_collector_restrictions():
	for c, in db("SELECT DISTINCT collector FROM collector_restrictions"):
		print '%s(%s) is restricted to:' % (get_obj_name(c), c)
		for obj, in db("SELECT object FROM collector_restrictions WHERE collector = ?", c):
			print '\t%s(%s)' % (get_obj_name(obj),obj)

functions = {
		'resources' : print_res,
		'units' : print_unit,
		'buildings' : print_building,
		'building_costs' : print_building_costs,
		'storage' : print_storage,
		'lines' : print_production_lines,
		'verbose_lines' : print_verbose_lines,
		'settler_lines' : print_settler_lines,
		'collectors' : print_collectors,
		'collector_restrictions': print_collector_restrictions,
		}
abbrevs = {
		'res' : 'resources',
		'b' : 'buildings',
		'building' : 'buildings',
		'bc' : 'building_costs',
		'vl' : 'verbose_lines',
		'sl' : 'settler_lines',
		'c': 'collectors',
		'cr': 'collector_restrictions',
		'unit': 'units',
		}

flags = dict(functions)
for (x,y) in abbrevs.iteritems(): # add convenience abbreviations to possible flags
	flags[x] = functions[y]

args = sys.argv

if len(args) == 1:
	print 'Start with one of those args: %s \nSupported abbreviations: %s' % (functions.keys(), abbrevs.keys())
else:
	for i in flags.iteritems():
		if i[0].startswith(args[1]):
			i[1]()
			sys.exit(0)
	print 'Start with one of those args: %s \nSupported abbreviations: %s' % (functions.keys(), abbrevs.keys())
