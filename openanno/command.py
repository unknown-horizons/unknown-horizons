# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import cPickle

class Command(object):
	"""Base class representing ingame commands"""
	
	def __init__(self):
		pass

	def can_execute(self):
		"""Return whether the command can be executed
		This might return details on why the action is not possible"""		
		raise Exception("Virtual function!")
	
	def serialize(self):
		"""Serialize the command to a string"""
		return cPickle.dumps(self)
	
	def unserialize(string):
		"""Unserialize the string to a command object"""
		obj = cPickle.loads(string)
		if not issubclass(obj, Command):
			raise UnpicklingError("Received object is not a subclass of openanno.Command")
# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import cPickle

class Command(object):
	"""Base class representing ingame commands"""
	
	def __init__(self):
		pass

	def can_execute(self):
		"""Return whether the command can be executed
		This might return details on why the action is not possible"""		
		raise Exception("Virtual function!")
	
	def serialize(self):
		"""Serialize the command to a string"""
		return cPickle.dumps(self)
	
	def unserialize(string):
		"""Unserialize the string to a command object"""
		obj = cPickle.loads(string)
		if not issubclass(obj, Command):
			raise UnpicklingError("Received object is not a subclass of openanno.Command")
# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import cPickle

class Command(object):
	"""Base class representing ingame commands"""
	
	def __init__(self):
		pass

	def can_execute(self):
		"""Return whether the command can be executed
		This might return details on why the action is not possible"""		
		raise Exception("Virtual function!")
	
	def serialize(self):
		"""Serialize the command to a string"""
		return cPickle.dumps(self)
	
	def unserialize(string):
		"""Unserialize the string to a command object"""
		obj = cPickle.loads(string)
		if not issubclass(obj, Command):
			raise UnpicklingError("Received object is not a subclass of openanno.Command")
# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import cPickle

class Command(object):
	"""Base class representing ingame commands"""
	
	def __init__(self):
		pass

	def can_execute(self):
		"""Return whether the command can be executed
		This might return details on why the action is not possible"""		
		raise Exception("Virtual function!")
	
	def serialize(self):
		"""Serialize the command to a string"""
		return cPickle.dumps(self)
	
	def unserialize(string):
		"""Unserialize the string to a command object"""
		obj = cPickle.loads(string)
		if not issubclass(obj, Command):
			raise UnpicklingError("Received object is not a subclass of openanno.Command")
# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import cPickle

class Command(object):
	"""Base class representing ingame commands"""
	
	def __init__(self):
		pass

	def can_execute(self):
		"""Return whether the command can be executed
		This might return details on why the action is not possible"""		
		raise Exception("Virtual function!")
	
	def serialize(self):
		"""Serialize the command to a string"""
		return cPickle.dumps(self)
	
	def unserialize(string):
		"""Unserialize the string to a command object"""
		obj = cPickle.loads(string)
		if not issubclass(obj, Command):
			raise UnpicklingError("Received object is not a subclass of openanno.Command")