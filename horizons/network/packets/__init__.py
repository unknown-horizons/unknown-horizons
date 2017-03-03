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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA	02110-1301	USA
# ###################################################

import cPickle
import inspect
import sys

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO # type: ignore

from horizons.network import NetworkException, PacketTooLarge

__version__ = '0.1'

PICKLE_PROTOCOL = 2
PICKLE_RECIEVE_FROM = 'server'
PICKLE_SAFE = {
	'client' : {},
	'server' : {},
} # type: Dict[str, Dict[str, Set[str]]]

class SafeUnpickler(object):
	"""
	NOTE: this is a security related method and may lead to
	execution of arbritary code if used in a wrong way

	pickle encodes modules and classes using their name. during "unpickling"
	pickle imports the modules and creates instances of these classes again.
	knowing this an attacker could easily create a paket "tricking" pickle
	to load and execute an instance of dangerous classes/methods/commands.
	this is not an exploit but by design!
	e.g. python -c 'import pickle; pickle.loads("cos\nsystem\n(S\"ls ~\"\ntR.")'

	In order to make pickle safer we build a whitelist of modules and classes
	which pickle will check during "unpickling". Please note that we aren't
	100% sure if there is still a way to execute arbitrary code.

	References:
	- http://docs.python.org/library/pickle.html
	- http://nadiana.com/python-pickle-insecure
	"""
	@classmethod
	def add(cls, origin, klass):
		"""Adding SafeUnpickler to the pickle whitelist"""
		global PICKLE_SAFE
		module = klass.__module__
		name  = klass.__name__
		if (module == cls.__module__ and name == cls.__name__):
			raise RuntimeError("Adding SafeUnpickler to the pickle whitelist is not allowed")
		types = ['client', 'server'] if origin == 'common' else [origin]
		for origin in types:
			if module not in PICKLE_SAFE[origin]:
				PICKLE_SAFE[origin][module] = set()
			if name not in PICKLE_SAFE[origin][module]:
				PICKLE_SAFE[origin][module].add(name)

	@classmethod
	def set_mode(cls, client=True):
		global PICKLE_RECIEVE_FROM
		if client:
			PICKLE_RECIEVE_FROM = 'server'
		else:
			PICKLE_RECIEVE_FROM = 'client'

	@classmethod
	def find_class(cls, module, name):
		global PICKLE_SAFE, PICKLE_RECIEVE_FROM
		if module not in PICKLE_SAFE[PICKLE_RECIEVE_FROM]:
			raise cPickle.UnpicklingError(
				'Attempting to unpickle unsafe module "{0}" (class="{1}")'.
				format(module, name))
		__import__(module)
		mod = sys.modules[module]
		if name not in PICKLE_SAFE[PICKLE_RECIEVE_FROM][module]:
			raise cPickle.UnpicklingError(
				'Attempting to unpickle unsafe class "{0}" (module="{1}")'.
				format(name, module))
		klass = getattr(mod, name)
		return klass

	@classmethod
	def loads(cls, str):
		file = StringIO(str)
		obj = cPickle.Unpickler(file)
		obj.find_global = cls.find_class
		return obj.load()

#-------------------------------------------------------------------------------

class packet(object):
	maxpacketsize = 0

	def __init__(self):
		"""ctor"""

	@staticmethod
	def validate(pkt, protocol):
		return True

	def serialize(self):
		return cPickle.dumps(self, PICKLE_PROTOCOL)

#-------------------------------------------------------------------------------

class cmd_ok(packet):
	"""simple ok message"""

SafeUnpickler.add('common', cmd_ok)

#-------------------------------------------------------------------------------

class cmd_error(packet):
	def __init__(self, errorstr, _type=0):
		self.errorstr = errorstr
		self.type = _type

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.errorstr, str):
			raise NetworkException("Invalid datatype: errorstr")
		if not isinstance(pkt.type, int):
			raise NetworkException("Invalid datatype: type")

SafeUnpickler.add('common', cmd_error)

#-------------------------------------------------------------------------------

class cmd_fatalerror(packet):
	def __init__(self, errorstr):
		self.errorstr = errorstr

	@staticmethod
	def validate(pkt, protocol):
		if not isinstance(pkt.errorstr, str):
			raise NetworkException("Invalid datatype: errorstr")

SafeUnpickler.add('common', cmd_fatalerror)

#-------------------------------------------------------------------------------

def unserialize(data, validate=False, protocol=0):
	mypacket = SafeUnpickler.loads(data)
	if validate:
		if not inspect.isfunction(mypacket.validate):
			raise NetworkException("Attempt to override packet.validate()")
		if mypacket.__class__.maxpacketsize > 0 and len(data) > mypacket.__class__.maxpacketsize:
			raise PacketTooLarge("packet={}, length={:d})".format(mypacket.__class__.__name__, len(data)))
		mypacket.__class__.validate(mypacket, protocol)
	return mypacket

#-------------------------------------------------------------------------------

import horizons.network.packets.server
import horizons.network.packets.client
