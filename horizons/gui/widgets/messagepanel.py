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
import logging

from fife.extensions import pychan

import horizons.globals

from horizons.extscheduler import ExtScheduler
from horizons.util.living import LivingObject
from horizons.gui.util import load_uh_widget

class MessagePanel(LivingObject):
	log = logging.getLogger('gui.widgets.messagepanel')

	def __init__(self, session):
		super(MessagePanel, self).__init__()
		self.session = session
		self.minimized = False
		self.actions = {}

		self.widget = load_uh_widget("messagepanel.xml")
		self.widget.position = (-10, horizons.globals.fife.engine_settings.getScreenHeight() - self.widget.size[1])
		self.widget.mapEvents({ 'min_max': self.minimize_maximize })

		self.widget.show()

		ExtScheduler().add_new_object(self.tick, self, loops=-1)
		self.draw_widget()

	def draw_widget(self):
		container = self.widget.findChild(name="tasks")
		container.removeAllChildren()
		if self.session.scenario_eventhandler.current_action:
			action = self.session.scenario_eventhandler.current_action
			title = unicode(action.arguments[1])
			self.actions[action.arguments[0]] = title
			hbox = pychan.HBox()
			hbox.addChild(pychan.Icon(image="content/gui/images/buttons/right_10_h.png"))
			hbox.addChild(pychan.Label(text=title))
			container.addChild(hbox)

			for old_title in reversed(self.actions.values()):
				if old_title == action.arguments[1]:
					continue
				hbox = pychan.HBox()
				hbox.addChild(pychan.Icon(image="content/gui/images/buttons/right_10.png"))
				hbox.addChild(pychan.Label(text=old_title))
				container.addChild(hbox)

		self.widget.adaptLayout()

	def minimize_maximize(self):
		button = self.widget.findChild(name='min_max')
		if not self.minimized:
			self.widget.position = (-10, horizons.globals.fife.engine_settings.getScreenHeight() - 19)
			self.minimized = True

			button.up_image = "content/gui/images/buttons/up_10_h.png"
			button.down_image = "content/gui/images/buttons/up_10.png"
			button.hover_image = "content/gui/images/buttons/up_10_h.png"
		else:
			self.widget.position = (-10, horizons.globals.fife.engine_settings.getScreenHeight() - self.widget.size[1])
			self.minimized = False

			button.up_image = "content/gui/images/buttons/down_10_h.png"
			button.down_image = "content/gui/images/buttons/down_10.png"
			button.hover_image = "content/gui/images/buttons/down_10_h.png"

	def tick(self):
		self.draw_widget()

	def end(self):
		ExtScheduler().rem_all_classinst_calls(self)
		super(MessagePanel, self).end()
