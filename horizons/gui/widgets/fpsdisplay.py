# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from fife.extensions.pychan.widgets import ABox, Label

import horizons.globals
from horizons.engine import Fife
from horizons.extscheduler import ExtScheduler


class FPSDisplay(ABox):
	"""Display the frames per second.

	Updates once a second if visible.
	"""

	def __init__(self):
		super(FPSDisplay, self).__init__()

		self._label = Label(text=u"- - -")
		self.addChild(self._label)
		self.stylize('menu')
		self.position_technique = "left:bottom"

		self._timemanager = horizons.globals.fife.engine.getTimeManager()

	def _update(self):
		fps = 1000 / self._timemanager.getAverageFrameTime()
		self._label.text = u"FPS: %.1f" % fps
		self.resizeToContent()
		self.toggle()  # hide and show again to fix position (pychan...)
		self.toggle()

	def show(self):
		ExtScheduler().add_new_object(self._update, self, loops=-1)
		return super(FPSDisplay, self).show()

	def hide(self):
		ExtScheduler().rem_call(self, self._update)
		return super(FPSDisplay, self).hide()

	def toggle(self):
		if (Fife.getVersion() <= (0, 3, 5)):
			if self._visible:
				self.hide()
			else:
				self.show()
		else:
			if self.isSetVisible():
				self.hide()
			else:
				self.show()
