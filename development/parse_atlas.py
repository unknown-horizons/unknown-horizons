#!/usr/bin/env python

# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import sys
import os
import glob

sys.path.append(".")

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
from horizons.util import ActionSetLoader, TileSetLoader

# Dummy fife object for
class DummyFife:
	use_atlases = False
horizons.main.fife = DummyFife()

class AtlasEntry(object):
	def __init__(self, source, xpos, ypos, width, height):
		self.source = source
		self.xpos = xpos
		self.ypos = ypos
		self.width = width
		self.height = height
		self.file = ""

# We add info of every atlases to .sql file
try:
	f = open(os.path.join("development", "atlas", "atlas.sql"), "w+")
	print >> f, "CREATE TABLE atlas('atlas_id' INTEGER NOT NULL PRIMARY KEY, 'atlas_path' TEXT NOT NULL);"
except IOError as e:
	print e.message
	print 'Please make sure you have', os.path.join("development", "atlas"), "directory populated with atlas files."
	sys.exit(1)
atlases = {}
mapping = {}

# Parse every .xml atlas file in this directory
atlas_xml_files = glob.glob(os.path.join("development", "atlas", "*.xml"))
atlas_xml_files.sort()

from xml.dom import minidom

for i, atlas_xml_file in enumerate(atlas_xml_files):
	print "Parsing: " + atlas_xml_file
	doc = minidom.parse(atlas_xml_file)
	root = doc.getElementsByTagName("atlas")[0]
	atlas = root.getAttribute("name")
	atlas_src = "/".join(["content", "gfx", "atlas", atlas])
	print >> f, "INSERT INTO atlas VALUES({0}, '{1}');".format(i, atlas_src)
	atlases[atlas] = i

	for node in root.childNodes:
		if node.nodeType == minidom.Node.ELEMENT_NODE and node.nodeName == "image":
			source = node.getAttribute("source")
			xpos = int(node.getAttribute("xpos"))
			ypos = int(node.getAttribute("ypos"))
			width = int(node.getAttribute("width"))
			height = int(node.getAttribute("height"))
			if source in mapping:
				print 'Warning: {0} is defined in more than one atlases'.format(source)
			mapping[source] = AtlasEntry(atlas, xpos, ypos, width, height)
print ""
f.close()

not_found = 0
deleted = []

for source in mapping:
	if not os.path.exists(source):
		deleted.append(source)

if deleted:
	deleted.sort()
	print "Unused atlas entry:"
	for v in deleted:
		print "  {0} (in {1})".format(v, mapping[v].source)
	print ""

# Modify a bit how all_action_sets looks like
all_action_sets = ActionSetLoader.get_sets()
for tileset_id in all_action_sets:
	for action_id in all_action_sets[tileset_id]:
		for rotation in sorted(all_action_sets[tileset_id][action_id]):
			for file in sorted(all_action_sets[tileset_id][action_id][rotation]):
				# File name is only there for image manager to have unique names, it really doesn't matter
				# if its '/' or '\\' or even ':', we just need to pick one
				file_new = file.replace('\\', '/')

				try:
					entry = mapping[file_new]
				except KeyError:
					print "Warning: {0} not found".format(file)
					not_found = not_found + 1
					continue

				# Instead of only float value we need to hold a 'bit' more infos in all_action_sets dictionary
				animval = all_action_sets[tileset_id][action_id][rotation][file]
				del all_action_sets[tileset_id][action_id][rotation][file]
				all_action_sets[tileset_id][action_id][rotation][file_new] = [animval, \
					atlases[entry.source], entry.xpos, entry.ypos, entry.width, entry.height]

# Dump it into JSON file
import json
with open(os.path.join("development", "atlas", "actionsets.json"), mode="wb") as fjson:
	json.dump(all_action_sets, fjson, indent=1)

# Same stuff with tilesets
all_tile_sets = TileSetLoader.get_sets()
for tileset_id in all_tile_sets:
	for action_id in all_tile_sets[tileset_id]:
		for rotation in sorted(all_tile_sets[tileset_id][action_id]):
			for file in sorted(all_tile_sets[tileset_id][action_id][rotation]):

				file_new = file.replace('\\', '/')

				try:
					entry = mapping[file_new]
				except KeyError:
					print "Warning: {0} not found".format(file)
					not_found = not_found + 1
					continue

				animval = all_tile_sets[tileset_id][action_id][rotation][file]
				del all_tile_sets[tileset_id][action_id][rotation][file]
				all_tile_sets[tileset_id][action_id][rotation][file_new] = [animval, \
					atlases[entry.source], entry.xpos, entry.ypos, entry.width, entry.height]

# Dump it into JSON file
import json
with open(os.path.join("development", "atlas", "tilesets.json"), mode="wb") as fjson:
	json.dump(all_tile_sets, fjson, indent=1)

print "Parsing done ..."
if not_found > 0:
	print "Total not found images: ", not_found
print ""

import shutil
print "Copying atlas.sql to", os.path.join("content", "atlas.sql")
shutil.copyfile(os.path.join("development","atlas", "atlas.sql"), os.path.join("content", "atlas.sql"))
print "Copying actionsets.json to", os.path.join("content", "actionsets.json")
shutil.copyfile(os.path.join("development","atlas", "actionsets.json"), os.path.join("content", "actionsets.json"))
print "Copying tilesets.json to", os.path.join("content", "tilesets.json")
shutil.copyfile(os.path.join("development","atlas", "tilesets.json"), os.path.join("content", "tilesets.json"))
print ""

atlas_path = os.path.join("content", "gfx", "atlas")
if os.path.exists(atlas_path) == False:
	os.mkdir(atlas_path)

for image in glob.glob(os.path.join("development", "atlas", "*.png")):
	dest  = os.path.join(atlas_path, os.path.basename(image))
	print "Copying", image, "to", dest
	shutil.copyfile(image, dest)
print "\nAll done\n"