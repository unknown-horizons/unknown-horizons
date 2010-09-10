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
gettext.install('')

from run_uh import init_environment
init_environment()

import horizons.main

db = horizons.main._create_db()

def get_obj_name(obj):
	global db
	if obj < 1000000:
		return db("SELECT name FROM building where id = ?", obj)[0][0]
	else:
		return db("SELECT name FROM unit where id = ?", obj)[0][0]

def get_res_name(res):
	global db
	return db("SELECT name FROM resource WHERE id = ?", res)[0][0]

def print_production_lines():
	print 'Production Lines:'
	for prod_line in db("SELECT id, object_id, time, enabled_by_default FROM production_line ORDER BY object_id"):
		id = prod_line[0]
		object = prod_line[1]

		str = 'ProdLine %s of %s (time:%s;default:%s):\t' % (id, get_obj_name(object), prod_line[2], prod_line[3])
		str = strw(str, 55)

		consumation = db("SELECT resource, amount FROM balance.production WHERE production_line = ? AND amount < 0 ORDER BY amount ASC", id)
		if len(consumation) > 0:
			str += 'consumes: '
			for res, amount in consumation:
				str += '%s %s, ' % (-amount, get_res_name(res))

		production = db("SELECT resource, amount FROM balance.production WHERE production_line = ? AND amount > 0 ORDER BY amount ASC", id)
		if len(production) > 0:
			str += '\tproduces: '
			for res, amount in production:
				str +=  '%s %s, ' % (amount, get_res_name(res))

		print str


def strw(s, width=0):
	"""returns sing with at least width chars"""
	s = str(s)
	slen = len(s)
	diff = width - slen
	if diff > 0: s += " "*diff
	return s


def print_res():
	print "Resources (id: resource (value))"
	for id, name, value in db("SELECT id, name, value FROM resource"):
		print "%s:\t%s (%s)" % (id, name, value)

def print_building():
	print "Buildings (id: name running_costs from class, size, radius):"
	for id, name, c_type, c_package, x, y, radius, cost in \
			db('SELECT id, name, class_type, class_package, size_x, size_y, radius, cost_active FROM \
			building LEFT OUTER JOIN balance.building_running_costs ON balance.building_running_costs.building = building.id'):
		cost = " 0" if cost is None else cost
		print "%s: %s %s$, from %s.%s, %sx%s, %s" % (strw(id,2), strw(name, 16), strw(cost, 2), c_package, c_type, x, y, radius)

def print_unit():
	print "Units (id: name from class)"
	for id, name, c_type, c_package in db("SELECT id, name, class_type, class_package FROM unit"):
		print "%s: %s from %s.%s" % (id, strw(name, 22), c_package, c_type)

def print_storage():
	for (obj, ) in db('SELECT DISTINCT object_id FROM storage'):
		print get_obj_name(obj), 'can store:'
		for res, amount in db("SELECT resource, size FROM storage WHERE object_id = ?", obj):
			print "\t%s tons of %s" % (amount, get_res_name(res))
	print "\nAll others can store 30 tons of each res."

def print_collectors():
	print 'Collectors: (building count collector)'
	for b, coll, count in db("SELECT object_id, collector_class, count FROM \
			collectors ORDER BY object_id ASC"):
		print "%s %s %s" % ( strw(get_obj_name(b), 18), count, get_obj_name(coll))

def print_building_costs():
	print 'Building costs:'
	for b, in db("SELECT DISTINCT building FROM balance.building_costs"):
		s = strw(get_obj_name(b), 18)
		for res, amount in db("SELECT resource, amount FROM balance.building_costs WHERE building = ?", b):
			s += str(amount)+' '+get_res_name(res)+', '
		print s

def print_collector_restrictions():
	for c, in db("SELECT DISTINCT collector FROM collector_restrictions"):
		print get_obj_name(c), 'is restricted to:'
		for obj, in db("SELECT object FROM collector_restrictions WHERE collector = ?", c):
			print '\t%s' % get_obj_name(obj)

functions = {
		'res' : print_res,
		'building' : print_building,
		'unit' : print_unit,
		'storage' : print_storage,
		'lines' : print_production_lines,
		'collectors' : print_collectors,
		'bc' : print_building_costs,
		'building_costs' : print_building_costs,
    'collector_restrictions': print_collector_restrictions,
		}

args = sys.argv

if len(args) == 1:
	print 'Start with one of those args: %s' % functions.keys()
else:
	for i in functions.iteritems():
		if i[0].startswith(args[1]):
			i[1]()
			sys.exit(0)
	print 'Start with one of those args: %s' % functions.keys()

