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

import pychan

from pychan.widgets.common import UnicodeAttr
from horizons.i18n import load_xml_translated

class TooltipIcon(pychan.widgets.Icon):
	ATTRIBUTES = pychan.widgets.Icon.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, **kwargs):
		super(TooltipIcon, self).__init__(**kwargs)
		self.gui = load_xml_translated('tooltip.xml')
		self.gui.hide()
		self.mapEvents({
			self.name + '/mouseEntered' : self.show_tooltip,
			self.name + '/mouseExited' : self.gui.hide
			})

	def test(self):
		print self.name

	def show_tooltip(self):
		if hasattr(self, 'tooltip'):
			self.label = self.gui.findChild(name='tooltip')
			self.label.text = self.tooltip
			self.gui.show()
		else:
			pass

