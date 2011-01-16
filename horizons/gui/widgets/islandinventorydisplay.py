# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

class SettlementInventoryDisplay(object):
	"""
	Contains methods that create and modify the bar when player hovers own
	settlements, displaying the inventory amount of several resources.
	Also takes care of the building cost display (in build preview mode) and
	the gold amount display which is always active (non-settlement-depending).
	"""
	def update_gold(self):
		first = str(self.session.world.player.inventory[RES.GOLD_ID])
		lines = []
		show = False
		if self.resource_source is not None and self.resources_needed.get(RES.GOLD_ID, 0) != 0:
			show = True
			lines.append('- ' + str(self.resources_needed[RES.GOLD_ID]))
		self.status_set('gold', first)
		self.status_set_extra('gold',lines)
		self.set_status_position('gold')
		if show:
			self.widgets['status_extra_gold'].show()
		else:
			self.widgets['status_extra_gold'].hide()

	def status_set(self, label, value):
		"""Sets a value on the status bar (settlement inventory amount of the res).
		@param label: str containing the name of the label to be set.
		@param value: value the Label is to be set to.
		"""
		if isinstance(value,list):
			value = value[0]
		gui = self.widgets['status_gold'] if label == 'gold' else self.widgets['status']
		foundlabel = gui.child_finder(label + '_1')
		foundlabel._setText(unicode(value))
		foundlabel.resizeToContent()
		gui.resizeToContent()

	def status_set_extra(self,label,value):
		"""Sets a value on the extra status bar. (below normal status bar, needed res for build)
		@param label: str containing the name of the label to be set.
		@param value: value the Label is to be set to.
		"""
		bg_icon_gold = "content/gui/images/background/widgets/res_mon_extra_bg.png"
		bg_icon_res = "content/gui/images/background/widgets/res_extra_bg.png"
		pos = {'gold':(14,83), 'food':(0,6), 'tools':(52,6), 'boards':(104,6), 'bricks':(156,6), 'textiles':(207,6)}
		#TODO replace this with a customizable widget (which resources are shown)
		if not hasattr(self, "bg_icon_pos"):
			self.bg_icon_pos = pos 
			self.bgs_shown = {}
		bg_icon = pychan.widgets.Icon(image=bg_icon_gold if label == 'gold' else bg_icon_res, \
		                              position=self.bg_icon_pos[label], name='bg_icon_' + label)
		if isinstance(value, str):
			value = [value]
		if label == 'gold':
			self._set_label_text('status_extra_gold', bg_icon, label, value)
		else:
			self._set_label_text('status_extra', bg_icon, label, value)

	def _set_label_text(self, widget, bg_icon, label, value):
		if not value:
			foundlabel = self.widgets[widget].child_finder(label + '_' + str(2))
			foundlabel.text = u''
			foundlabel.resizeToContent()
			if label in self.bgs_shown:
				self.widgets[widget].removeChild(self.bgs_shown[label])
				del self.bgs_shown[label]
			self.widgets[widget].resizeToContent()
			# remove any displayed label for this resource and the corresponding icons
			return

		if self.widgets[widget].findChild(name='bg_icon_' + label) is None:
			self.widgets[widget].insertChild(bg_icon, 0)
			self.bgs_shown[label] = bg_icon
			# display background icon

		for i in xrange(0,len(value)): #TODO examine what this loop does
			text = value[i]
			foundlabel = self.widgets[widget].child_finder(name=label + '_' + str(i+2))
			foundlabel._setText(unicode(text))
			foundlabel.resizeToContent()
			# display the amount of a particular resource that your construction will cost
		self.widgets[widget].resizeToContent()

	def resourceinfo_set(self, source, res_needed = {}, res_usable = {}, res_from_ship = False):
		city = source if not res_from_ship else None
		self.cityinfo_set(city)
		if source is not self.resource_source:
			if self.resource_source is not None:
				self.resource_source.remove_change_listener(self.update_resource_source)
			if source is None or self.session.world.player != source.owner:
				self.widgets['status'].hide()
				self.widgets['status_extra'].hide()
				self.resource_source = None
				self.update_gold()
		if source is not None and self.session.world.player == source.owner:
			if source is not self.resource_source:
				source.add_change_listener(self.update_resource_source)
			self.resource_source = source
			self.resources_needed = res_needed
			self.resources_usable = res_usable
			self.update_resource_source()
			self.widgets['status'].show()

	def update_resource_source(self):
		"""Sets the values for resource status bar as well as the building costs"""
		self.update_gold()
		for res_id, res_name in {3 : 'textiles', 4 : 'boards', 5 : 'food', 6 : 'tools', 7 : 'bricks'}.iteritems():
			first = str(self.resource_source.inventory[res_id])
			lines = []
			show = False
			if self.resources_needed.get(res_id, 0) != 0:
				show = True
				lines.append('- ' + str(self.resources_needed[res_id]))
			self.status_set(res_name, first)
			self.status_set_extra(res_name,lines)
			self.set_status_position(res_name)
			if show:
				self.widgets['status_extra'].show()

	def set_status_position(self, resource_name):
		"""Sets the position of the labels displaying current inventory amount
		and the costs of the building the player activated the build preview of.
		@param resource_name: string used to look up xml elements containing this.
		"""
		icon_name = resource_name + '_icon'
		for i in xrange(1, 3): # loop values 1 and 2
			lbl_name = resource_name + '_' + str(i)
			# e.g. tools_1 = inventory amount, tools_2 = cost of to-be-built building
			if resource_name == 'gold':
				self._set_label_position('status_gold', lbl_name, icon_name, 33, 31 + i*20)
			else:
				self._set_label_position('status', lbl_name, icon_name, 24, 31 + i*20)

	def _set_label_position(self, widget, lbl_name, icon_name, xoffset, yoffset):
		icon  = self.widgets[widget].child_finder(icon_name)
		label = self.widgets[widget].child_finder(lbl_name)
		label.position = (icon.position[0] - label.size[0]/2 + xoffset, yoffset)
