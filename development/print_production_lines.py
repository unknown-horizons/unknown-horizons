#!/usr/bin/env python

import os.path
import sys

dbfile = 'content/game.sqlite'

if not os.path.exists(dbfile):
	print 'please run from uh root dir'
	sys.exit(1)

sys.path.append(".")
sys.path.append("./horizons")

import environment
environment.init()

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

