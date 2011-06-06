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

#from horizons.util import decorators

########################################################################
class IconPathFinder(object):
	"""
	Generates and caches paths to various dynamic icons.
	Currently used for resource icons.
	"""
#	@decorators.cachedmethod
	def get_res_icon(res):
		"""Returns icons of a resource
		@param res: resource id
		@return: tuple: (icon_path, icon_disabled_path)"""
		#TODO move to proper place now that we no longer use the db
		ICON_PATH = 'content/gui/icons/resources/'
		icon = ICON_PATH + '50/%03d.png' % res
		icon_disabled = ICON_PATH + '50/greyscale/%03d.png' % res
		icon_small = ICON_PATH + '16/%03d.png' % res
		return (icon, icon_disabled, icon_small)
