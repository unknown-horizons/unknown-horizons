# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

import os

class PluginManager:
	""" Currently, pluginmanager iterates through the plugin directory
	adding the plugins if they are set to True in settings.xml. If a plugin
	isn't set in settings.xml it assumes it is not to be loaded, and saves it
	as False in settings.xml.
	
	If a plugin fails to load due to exceptions, they are caught and a line
	of the error is printed to console.
	"""
	def __init__(self, settings, *args, **kwargs):
		self._settings = settings
		
		self._pluginDir = "plugins"
		self._plugins = []
		
		files = []
		for f in os.listdir(self._pluginDir):
			path = os.path.join(self._pluginDir, f)
			if os.path.isfile(path) and os.path.splitext(f)[1] == ".py" and f != "__init__.py":
				files.append(os.path.splitext(f)[0])
				
		for f in files:
			importPlugin = self._settings.get("Plugins", f, False)
			if importPlugin:
				try:
					print "Importing plugin:", f
					exec "import plugins."+f
					plugin = eval("plugins."+f+"."+f+"()")
					if isinstance(plugin, Plugin) is False:
						print f+" is not an instance of Plugin!"
					else:
						plugin.enable()
						self._plugins.append(plugin)
				except BaseException, error:
					print "Error: ", error
					print "Invalid plugin:", f
			else:
				print "Not importing plugin:", f
				
			self._settings.set("Plugins", f, importPlugin)
			
		self._settings.saveSettings()

		
class Plugin:
	""" The base class for all plugins. All plugins should override these functions. """
	
	def enable(self):
		raise NotImplementedError, "Plugin has not implemented the enable() function!"

	def disable(self):
		raise NotImplementedError, "Plugin has not implemented the disable() function!"

	def isEnabled(self):
		raise NotImplementedError, "Plugin has not implemented the isEnabled() function!"

	def getName(self):
		raise NotImplementedError, "Plugin has not implemented the getName() function!"
		
	#--- These are not so important ---#
	def getAuthor(self):
		return "Unknown"
		
	def getDescription(self):
		return ""

	def getLicense(self):
		return ""
		
	def getVersion(self):
		return "0.1"
