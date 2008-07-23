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

#because of unclean inheritance, bad usage of parameters and bad use of super in most world object, i cant trust that the init constructor is called.

class changelistener(object):
	def __init__(self, *args, **kwargs):
		super(changelistener, self).__init__(*args, **kwargs)
		self.__listeners = []

	def addChangeListener(self, listener):
		if not hasattr(self, '_changelistener__listeners'):
			self.__listeners = []
		self.__listeners.append(listener)

	def removeChangeListener(self, listener):
		if not hasattr(self, '_changelistener__listeners'):
			self.__listeners = []
		self.__listeners.remove(listener)

	def _changed(self):
		if not hasattr(self, '_changelistener__listeners'):
			self.__listeners = []
		for listener in self.__listeners:
			listener()
