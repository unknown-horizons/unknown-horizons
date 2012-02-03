#!/usr/bin/env python

"""
This script prints a html website containing an overview of our object action
sets in tabular layout. Objects include units and buildings unless restricted.
You usually want to redirect the output into a .html file.

#TODO: Implement the following:
Pass --no-units or --no-buildings to remove the respective entries.
For now, use the flags in lines 43ff.
"""

import os.path
import sys
import sqlite3

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
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.constants import UNITS

global db, loader, query
db = horizons.main._create_main_db()
loader = ActionSetLoader()
query = 'SELECT action_set_id FROM action_set WHERE object_id = ?'

get_buildings = True
#get_buildings = False
get_units = True
#get_units = False

def get_name(object_id):
	if object_id < UNITS.DIFFERENCE_BUILDING_UNIT_ID:
		name = db("SELECT name FROM building WHERE id = ?", object_id)[0][0]
		#query += ' ORDER BY settler_level ASC'
		#TODO this ORDER BY does not do what it was hired for.
	elif object_id > UNITS.DIFFERENCE_BUILDING_UNIT_ID:
		name = db("SELECT name FROM unit WHERE id = ?", object_id)[0][0]

	return name

def get_images(object_id):
	sets = []
	result_list = []

	for as_ in db(query, object_id):
		sets.append(as_[0])

	for as_ in sorted(sets): #TODO this sorted() call breaks order again, see above.
		set_ = loader.get_action_sets()[as_]
		try: #trees and roads have no idle animation
			image = set_['idle_full'][45].keys()[0]
		except KeyError:
			try:
				image = set_['idle'][45].keys()[0]
			except:
				image = set_['abc'][45].keys()[0]

		result_list.append(image)

	return result_list

def create_table_entry(object_id):
	WEBSITE = 'https://github.com/unknown-horizons/unknown-horizons/raw/master'
	retval = ''

	query = get_images(object_id)
	retval += '%s \n' % get_name(object_id)
	for result in query:
		retval += '<img src="%s/%s" alt="%s/" />\n' % (WEBSITE, result, result.split('content/gfx/')[1].split('/idle')[0])
	retval += '<hr />\n\n'
	return retval

def create_all_entries(id_list):
	retval = ''
	for id_ in sorted(id_list):
		retval += create_table_entry(id_)
	return retval

args = sys.argv


HEADER = \
'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title> Buildings and units in Unknown Horizons </title>
</head>
<body>'''

FOOTER = \
'''</body>
</html>'''

page = HEADER

if get_buildings:
	buildings = map(lambda x: x[0], db('SELECT DISTINCT id FROM building'))
	page += create_all_entries(buildings)

if get_units:
	units = map(lambda x: x[0], db('SELECT DISTINCT id FROM unit'))
	page += create_all_entries(units)

page += FOOTER

print page
