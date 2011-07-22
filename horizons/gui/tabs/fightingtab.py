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

from tabinterface import TabInterface
from horizons.util import Callback
from horizons.util.gui import load_uh_widget

class FightingUnitTab(TabInterface):

	def __init__(self, instance = None, widget = 'overview_fighting_unit.xml', \
	             icon_path='content/gui/icons/tabwidget/common/inventory_%s.png'):
		super(FightingUnitTab, self).__init__(widget = widget)
		self.instance = instance
		self.init_values()
		self.button_up_image = icon_path % 'u'
		self.button_active_image = icon_path % 'a'
		self.button_down_image = icon_path % 'd'
		self.button_hover_image = icon_path % 'h'
		self.tooltip = _("Fighting Tab")
		stance_widget = load_uh_widget('stancewidget.xml')
		self.widget.findChild(name='stance').addChild(stance_widget)
		self.toggle_stance()
		self.widget.mapEvents({
			'aggressive': Callback(self.set_stance, 'aggressive'),
			'hold_ground': Callback(self.set_stance, 'hold_ground'),
			'none': Callback(self.set_stance, 'none'),
			'flee': Callback(self.set_stance, 'flee')
			})

	def set_stance(self, stance):
		self.instance.set_stance(stance)
		self.toggle_stance()

	def toggle_stance(self):
		self.widget.findChild(name='aggressive').set_inactive()
		self.widget.findChild(name='hold_ground').set_inactive()
		self.widget.findChild(name='none').set_inactive()
		self.widget.findChild(name='flee').set_inactive()
		self.widget.findChild(name=self.instance.stance).set_active()

