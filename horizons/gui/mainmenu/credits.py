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

from horizons.gui.mainmenu import Dialog
from horizons.gui.widgets.imagebutton import OkButton
from horizons.util.python.callback import Callback


class Credits(Dialog):
	return_events = {OkButton.DEFAULT_NAME: True}

	def prepare(self, number=0, **kwargs):
		self._widget = self._widget_loader['credits{number}'.format(number=number)]
		for box in self._widget.findChildren(name='box'):
			box.margins = (30, 0) # to get some indentation
			if number in [0, 2]: # #TODO fix these hardcoded page references
				box.padding = 1
				box.parent.padding = 3 # further decrease if more entries

		labels = [self._widget.findChild(name=section+"_lbl")
		          for section in ('team', 'patchers', 'translators',
		                          'packagers', 'special_thanks')]

		for i in xrange(5): # add callbacks to each pickbelt
			labels[i].capture(Callback(self.dialogs.replace, self, number=i), event_name="mouseClicked")
