#!/usr/bin/env python

"""
This script prints a html website containing an overview of our object action
sets in tabular layout. Objects include units and buildings unless restricted.
You usually want to redirect the output into a .html file.

#TODO: Implement the following:
Pass --no-units or --no-buildings to remove the respective entries.
For now, use the flags in lines 43ff.
"""

get_buildings = True
get_units = True

WEBSITE = 'https://github.com/unknown-horizons/unknown-horizons/raw/master'

###############################################################################

import sys

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
from horizons.util.loaders.actionsetloader import ActionSetLoader

global db, action_sets
db = horizons.main._create_main_db()
action_sets = ActionSetLoader.get_sets()

from horizons.entities import Entities
from horizons.ext.dummy import Dummy
from horizons.extscheduler import ExtScheduler
ExtScheduler.create_instance(Dummy()) # sometimes needed by entities in subsequent calls

def get_entities(type):
	ret = dict()
	for e in getattr(Entities, type).itervalues():
		level_sets = e.action_sets_by_level
		di = dict()
		for (level, list) in level_sets.iteritems():
			if list == []:
				continue
			images = []
			for set in list:
				images.append(get_images(set)[0])
			di[level] = images # only one for now. #TODO animations
		ret[e.name] = di
	return ret

def get_images(data):
	"""Pass action_set name. Returns a list of image paths, much like this:
	['content/gfx/buildings/settlers/agricultural/as_herbary0/idle/135/0.png',
	 'content/gfx/buildings/settlers/agricultural/as_herbary0/idle/225/0.png',
	 'content/gfx/buildings/settlers/agricultural/as_herbary0/idle/315/0.png',
	 'content/gfx/buildings/settlers/agricultural/as_herbary0/idle/45/0.png'] """
	if 'idle' in action_sets[data]:
		action = 'idle'
	elif 'idle_full' in action_sets[data]:
		action = 'idle_full'
	elif 'abc' in action_sets[data]:
		action = 'abc'
	else: # If no idle animation found, use the first you find
		action = action_sets[data].keys()[0]
	return sorted(action_sets[data][action][45])

def create_table(type):
	retval = ''
	for (name, data) in sorted(get_entities(type).items()):
		for (level, images) in data.iteritems():
			for image in images:
				retval += '<img src="%s/%s" alt="%s/" />\n' % (WEBSITE, image, image.split('content/gfx/')[1].split('/idle')[0])
			retval += '<br />\n'
		retval += '%s\n<br />\n' % name
		retval += '<hr />\n\n'
	return retval

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
	Entities.load_buildings(db, load_now=True)
	page += create_table('buildings')
if get_units:
	Entities.load_units(load_now=True)
	page += create_table('units')

page += FOOTER

print page
