# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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


import os

class ActionSetLoader(object):
	"""The ActionSetLoader loads action sets from a directory tree. The directories loaded
	begin with 'as_' to tell tell the loader that they are an action set. directory
	structure is as follows: <action_set>/<action>/<rotation>/<framenumber>.png
	for example that would be: fisher1/work/90/0.png
	Note that all directories exept for the rotation dir, all dirs have to be empty and
	must not include additional action sets.
	@param start_dir: directory that is used to begin search in
	"""
	def __init__(self, start_dir):
		self.start_dir = start_dir
		self.action_sets = None # will later store the action sets

	def _load_files(self, dir, time):
		"""Loads the files for a specific rotation
		@param dir: directory that the files are to loaded from. Example:
		            'content/gfx/units/lumberjack/work/90/'
		@return: dict containing 'file: anim_end' entries
		"""
		fl = {}
		for root, dirs, files in os.walk(dir):
			i = 1
			for file in sorted(files):
				fl[root+os.path.sep+file] = ((float(time)/1000)/len(files))*i
				i += 1
		return fl

	def _load_rotation(self, dir):
		"""Loads the rotations + files for a specific action
		@param dir: directory that the files are to loaded from. Example:
		            'content/gfx/units/lumberjack/work/'
		@return: dict containing 'rotation: filedict' entries. See _load_files for example.
		"""
		rotations = {}
		time = 1000
		dirs = os.listdir(dir)
		for dirname in dirs:
			if "tm_" in dirname:
				time = dirname.split('_')[1]
				print time
				dirs.remove(dirname)
				break
		for dirname in dirs:
			rotations[int(dirname)] = self._load_files(os.path.join(dir, dirname),time)
		return rotations


	def _load_action(self, dir):
		"""Loads the actions + rotations + files for a specific action
		@param dir: directory that the files are to loaded from. Example:
		            'content/gfx/units/lumberjack/'
		@return: dict containing 'action: rotationdict' entries. See _load_rotation for example.
		"""
		actions = {}
		for dirname in os.listdir(dir):
			actions[dirname] = {}
			actions[dirname] = self._load_rotation(os.path.join(dir, dirname))
		return actions

	def load(self):
		print "Loading action_sets..."
		self.action_sets = {}
		for root, dirs, files in os.walk(self.start_dir):
			if "as_" in os.path.basename(root):
				self.action_sets[os.path.basename(root)] = self._load_action(root)
		print "Done!"

		for key, value in self.action_sets.iteritems():
			print "Action_set:" , key
			for key1, value1 in value.iteritems():
				print "Action:", key1
				for key2, value2 in value1.iteritems():
					print "Rotation:", key2
					for key3, value3 in value2.iteritems():
						print "File:", key3, "length:", value3
		return self.action_sets