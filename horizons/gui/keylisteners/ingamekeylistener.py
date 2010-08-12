# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from fife import fife
import horizons.main

from horizons.util.living import LivingObject

class IngameKeyListener(fife.IKeyListener, LivingObject):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self, session):
		super(IngameKeyListener, self).__init__()
		self.session = session
		horizons.main.fife.eventmanager.addKeyListenerFront(self)
		self.keysPressed = []
		# Used to sum up the keyboard autoscrolling
		self.key_scroll = [0, 0]

	def end(self):
		horizons.main.fife.eventmanager.removeKeyListener(self)
		self.session = None
		super(IngameKeyListener, self).end()

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()

		was = keyval in self.keysPressed
		if not was:
			self.keysPressed.append(keyval)
		if keyval == fife.Key.LEFT:
			if not was: self.key_scroll[0] -= 25
		if keyval == fife.Key.RIGHT:
			if not was: self.key_scroll[0] += 25
		if keyval == fife.Key.UP:
			if not was: self.key_scroll[1] -= 25
		if keyval == fife.Key.DOWN:
			if not was: self.key_scroll[1] += 25

		# We scrolled, do autoscroll
		if self.key_scroll[0] != 0 or self.key_scroll != 0:
			self.session.view.autoscroll_keys(self.key_scroll[0], self.key_scroll[1])

		if keyval == fife.Key.ESCAPE:
			if not self.session.ingame_gui.on_escape():
				return # let the MainListener handle this
		elif keystr == 'g':
			gridrenderer = self.session.view.renderer['GridRenderer']
			gridrenderer.setEnabled( not gridrenderer.isEnabled() )
		elif keystr == 'x':
			self.session.destroy_tool()
		elif keystr == '+':
			self.session.speed_up()
		elif keystr == '-':
			self.session.speed_down()
		elif keystr == 'p':
			self.session.ingame_gui.toggle_ingame_pause()
		elif keystr == 'd':
			pass
			#import pdb; pdb.set_trace()
			#debug code to check for memory leaks:
			"""
			import gc
			import weakref
			all_lists = []
			for island in self.session.world.islands:
				buildings_weakref = []
				for b in island.buildings:
					buildings_weakref.append( weakref.ref(b) )
				import random
				random.shuffle(buildings_weakref)
				all_lists.extend(buildings_weakref)

				for b in buildings_weakref:
					if b().id == 17: continue
					if b().id == 1: continue # bo is unremovable

					#if b().id != 2: continue # test storage now

					print 'gonna remove: ', b()
					b().remove()
					collected = gc.collect()
					print 'collected: ', collected

					if b() is not None:
						import pdb ; pdb.set_trace()
						print 'referrers: ', gc.get_referrers(b())
						a = gc.get_referrers(b())
						print

			#print all_lists
			"""

		elif keystr == 'b':
			self.session.ingame_gui.show_build_menu()
		elif keystr == '.':
			if hasattr(self.session.cursor, "rotate_right"):
				self.session.cursor.rotate_right()
		elif keystr == ',':
			if hasattr(self.session.cursor, "rotate_left"):
				self.session.cursor.rotate_left()
		elif keystr == 'c':
			self.session.ingame_gui.show_chat_dialog()
		elif keyval in (fife.Key.NUM_0, fife.Key.NUM_1, fife.Key.NUM_2, fife.Key.NUM_3, fife.Key.NUM_4, fife.Key.NUM_5, fife.Key.NUM_6, fife.Key.NUM_7, fife.Key.NUM_8, fife.Key.NUM_9):
			num = int(keyval - fife.Key.NUM_0)
			if evt.isControlPressed():
				self.session.selection_groups[num] = self.session.selected_instances.copy()
				for group in self.session.selection_groups:
					if group is not self.session.selection_groups[num]:
						group -= self.session.selection_groups[num]
			else:
				for instance in self.session.selected_instances - self.session.selection_groups[num]:
					instance.deselect()
				for instance in self.session.selection_groups[num] - self.session.selected_instances:
					instance.select()
				self.session.selected_instances = self.session.selection_groups[num]
		elif keyval == fife.Key.F5:
			self.session.quicksave()
		elif keyval == fife.Key.F9:
			self.session.quickload()
		else:
			return
		evt.consume()

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		try:
			self.keysPressed.remove(keyval)
		except:
			return
		if keyval == fife.Key.LEFT or \
		   keyval == fife.Key.RIGHT:
			self.key_scroll[0] = 0
		if keyval == fife.Key.UP or \
		   keyval == fife.Key.DOWN:
			self.key_scroll[1] = 0
		self.session.view.autoscroll_keys(self.key_scroll[0], self.key_scroll[1])

