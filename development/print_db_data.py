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

from run_uh import init_environment
init_environment()

from dbreader import DbReader

db = DbReader(dbfile)

def get_obj_name(obj):
	global db
	if obj < 1000000:
		return db("SELECT name FROM building where id = ?", obj)[0][0]
	else:
		return db("SELECT name FROM unit where id = ?", obj)[0][0]

def get_res_name(res):
	global db
	return db("Select name from resource where rowid = ?", res)[0][0]

def print_production_lines():
	print 'Production Lines:'
	for prod_line in db("SELECT id, object_id, time, enabled_by_default FROM production_line ORDER BY object_id"):
		id = prod_line[0]
		object = prod_line[1]

		str = ''
		str += 'ProdLine %s of %s (time:%s;default:%s):\t' % (id, get_obj_name(object), prod_line[2], prod_line[3])

		str += 'consumes: '
		for res, amount in db("SELECT resource, amount from production where production_line = ? and amount < 0 order by amount asc", id):
			str += '%s %s, ' % (-amount, get_res_name(res))

		str += ';\tproduces: '
		for res, amount in db("SELECT resource, amount from production where production_line = ? and amount > 0 order by amount asc", id):
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
	for id, name, value in db("select id, name, value from resource"):
		print "%s:\t%s (%s)" % (id, name, value)

def print_building():
	print "Buildings (id: name running_costs from class, size, radius):"
	for id, name, c_type, c_package, x, y, radius, cost in \
			db('select id, name, class_type, class_package, size_x, size_y, radius, cost_active from \
			building LEFT OUTER JOIN building_running_costs on building_running_costs.building = building.id'):
		cost = " 0" if cost is None else cost
		print "%s: %s %s$, from %s.%s, %sx%s, %s" % (strw(id,2), strw(name, 16), strw(cost, 2), c_package, c_type, x, y, radius)

def print_unit():
	print "Units (id: name from class)"
	for id, name, c_type, c_package in db("select id, name, class_type, class_package from unit"):
		print "%s: %s from %s.%s" % (id, strw(name, 22), c_package, c_type)

def print_storage():
	for (obj, ) in db('select distinct object_id from storage'):
		print get_obj_name(obj), 'can store:'
		for res, amount in db("select resource, size from storage where object_id = ?", obj):
			print "\t%s tons of %s" % (amount, get_res_name(res))
	print "\nAll others can store 30 tons of each res."

def print_collectors():
	print 'Collectors: (building count collector)'
	for b, coll, count in db("select object_id, collector_class, count from \
			collectors order by object_id asc"):
		print "%s %s %s" % ( strw(get_obj_name(b), 18), count, get_obj_name(coll))

functions = {
		'res' : print_res,
		'b' : print_building,
		'building' : print_building,
		'unit' : print_unit,
		'storage' : print_storage,
		'lines' : print_production_lines,
		'coll' : print_collectors,
		'collectors' : print_collectors,
		}

args = sys.argv

if len(args) == 1:
	print 'Start with one of those args: %s' % functions.keys()
else:
	functions[ args[1] ]()
