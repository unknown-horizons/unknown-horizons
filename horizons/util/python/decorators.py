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

"""Save general python function decorators here"""

from types import FunctionType, ClassType

class cachedfunction(object):
	"""Decorator that caches a function's return value each time it is called.
	If called later with the same arguments, the cached value is returned, and
	not re-evaluated.
	Does not support kwargs, since dicts are not hashable
	"""
	def __init__(self, func):
		self.func = func
		self.cache = {}

	def __call__(self, *args):
		try:
			return self.cache[args]
		except KeyError:
			self.cache[args] = value = self.func(*args)
			return value
		except TypeError:
			assert False, "Supplied invalid argument to cache decorator"


class cachedmethod(object):
	"""Same as cachedfunction, but works also for methods. Results are saved per instance"""
	def __init__(self, func):
		self.cache={}
		self.func=func

	def __get__(self, instance, cls=None):
		self.instance = instance
		return self

	def __call__(self,*args):
		instance = self.instance
		try:
			return self.cache[(instance, args)]
		except KeyError:
			self.cache[(instance,args)] = value = self.func(instance, *args)
			return value
		except TypeError:
			assert False, "Supplied invalid argument to cache decorator"


# adapted from http://code.activestate.com/recipes/277940/

from opcode import opmap, HAVE_ARGUMENT, EXTENDED_ARG
globals().update(opmap)

def _make_constants(f, builtin_only=False, stoplist=[], verbose=False):
	try:
		co = f.func_code
	except AttributeError:
		return f        # Jython doesn't have a func_code attribute.
	newcode = map(ord, co.co_code)
	newconsts = list(co.co_consts)
	names = co.co_names
	codelen = len(newcode)

	import __builtin__
	env = vars(__builtin__).copy()
	if builtin_only:
		stoplist = dict.fromkeys(stoplist)
		stoplist.update(f.func_globals)
	else:
		env.update(f.func_globals)

	# First pass converts global lookups into constants
	i = 0
	while i < codelen:
		opcode = newcode[i]
		if opcode in (EXTENDED_ARG, STORE_GLOBAL):
			return f    # for simplicity, only optimize common cases
		if opcode == LOAD_GLOBAL:
			oparg = newcode[i+1] + (newcode[i+2] << 8)
			name = co.co_names[oparg]
			if name in env and name not in stoplist:
				value = env[name]
				for pos, v in enumerate(newconsts):
					if v is value:
						break
				else:
					pos = len(newconsts)
					newconsts.append(value)
				newcode[i] = LOAD_CONST
				newcode[i+1] = pos & 0xFF
				newcode[i+2] = pos >> 8
				if verbose:
					print name, '-->', value
		i += 1
		if opcode >= HAVE_ARGUMENT:
			i += 2

	# Second pass folds tuples of constants and constant attribute lookups
	i = 0
	while i < codelen:

		newtuple = []
		while newcode[i] == LOAD_CONST:
			oparg = newcode[i+1] + (newcode[i+2] << 8)
			newtuple.append(newconsts[oparg])
			i += 3

		opcode = newcode[i]
		if not newtuple:
			i += 1
			if opcode >= HAVE_ARGUMENT:
				i += 2
			continue

		if opcode == LOAD_ATTR:
			obj = newtuple[-1]
			oparg = newcode[i+1] + (newcode[i+2] << 8)
			name = names[oparg]
			try:
				value = getattr(obj, name)
			except AttributeError:
				continue
			deletions = 1

		elif opcode == BUILD_TUPLE:
			oparg = newcode[i+1] + (newcode[i+2] << 8)
			if oparg != len(newtuple):
				continue
			deletions = len(newtuple)
			value = tuple(newtuple)

		else:
			continue

		reljump = deletions * 3
		newcode[i-reljump] = JUMP_FORWARD
		newcode[i-reljump+1] = (reljump-3) & 0xFF
		newcode[i-reljump+2] = (reljump-3) >> 8

		n = len(newconsts)
		newconsts.append(value)
		newcode[i] = LOAD_CONST
		newcode[i+1] = n & 0xFF
		newcode[i+2] = n >> 8
		i += 3
		if verbose:
			print "new folded constant:", value

	codestr = ''.join(map(chr, newcode))
	codeobj = type(co)(co.co_argcount, co.co_nlocals, co.co_stacksize,
				             co.co_flags, codestr, tuple(newconsts), co.co_names,
				             co.co_varnames, co.co_filename, co.co_name,
				             co.co_firstlineno, co.co_lnotab, co.co_freevars,
				             co.co_cellvars)
	return type(f)(codeobj, f.func_globals, f.func_name, f.func_defaults,
				         f.func_closure)

_make_constants = _make_constants(_make_constants) # optimize thyself!

def bind_all(mc, builtin_only=False, stoplist=None, verbose=False):
	"""Recursively apply constant binding to functions in a module or class.

	Use as the last line of the module (after everything is defined, but
	before test code).  In modules that need modifiable globals, set
	builtin_only to True.

	"""

	# Ignore gettext functions. At the beginning these point to a NullTranslation
	# object, they change when a language is activated.
	stoplist = stoplist or []
	stoplist.extend(['_', 'N_'])

	try:
		d = vars(mc)
	except TypeError:
		return
	for k, v in d.items():
		if type(v) is FunctionType:
			newv = _make_constants(v, builtin_only, stoplist,  verbose)
			setattr(mc, k, newv)
		elif type(v) in (type, ClassType):
			bind_all(v, builtin_only, stoplist, verbose)

@_make_constants
def make_constants(builtin_only=False, stoplist=[], verbose=False):
	""" Return a decorator for optimizing global references.

	Replaces global references with their currently defined values.
	If not defined, the dynamic (runtime) global lookup is left undisturbed.
	If builtin_only is True, then only builtins are optimized.
	Variable names in the stoplist are also left undisturbed.
	Also, folds constant attr lookups and tuples of constants.
	If verbose is True, prints each substitution as is occurs

	"""
	if type(builtin_only) == type(make_constants):
		raise ValueError("The bind_constants decorator must have arguments.")
	return lambda f: _make_constants(f, builtin_only, stoplist, verbose)


# Taken from http://code.activestate.com/recipes/576563-cached-property/
# Licenced under MIT
# A cached property is a read-only property that is calculated on demand and automatically cached. If the value has already been calculated, the cached value is returned.

def cachedproperty(f):
	"""returns a cached property that is calculated by function f"""
	def get(self):
		try:
			return self._property_cache[f]
		except AttributeError:
			self._property_cache = {}
			x = self._property_cache[f] = f(self)
			return x
		except KeyError:
			x = self._property_cache[f] = f(self)
			return x

	return property(get)