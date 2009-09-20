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
from horizons.gui.widgets.tooltip import TooltipIcon

import horizons.main

def create_resource_icon(res_id, db):
	"""Creates a pychan icon for a resource.
	@param res_id:
	@param db: dbreader for main db"""
	return TooltipIcon(tooltip=db("SELECT name FROM resource WHERE id = ?", res_id)[0][0], \
	                   image=db("SELECT icon FROM resource WHERE id = ?", res_id)[0][0])

def center_widget(widget):
	"""Centers the widget in the parameter
	@param widget: Widget with properties width, height, x and y
	"""
	widget.x = int((horizons.main.settings.fife.screen.width - widget.width) / 2)
	widget.y = int((horizons.main.settings.fife.screen.height - widget.height) / 2)
