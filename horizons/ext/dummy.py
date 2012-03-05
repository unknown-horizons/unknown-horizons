"""
Copyright (c) 2008 nosklo

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# http://code.activestate.com/recipes/576447-dummy-object/
# with some modifications

class Dummy(object):
	def __getattr__(self, attr):
		try:
			return super(self.__class__, self).__getattr__(attr)
		except AttributeError:
			if attr in ('__base__', '__bases__', '__basicsize__', '__cmp__',
				'__dictoffset__', '__flags__', '__itemsize__',
				'__members__', '__methods__', '__mro__', '__name__',
				'__subclasses__', '__weakrefoffset__',
				'_getAttributeNames', 'mro'):
				raise
			else:
				return self
	def next(self):
		raise StopIteration
	def __repr__(self):
		return 'Dummy()'
	def __init__(self, *args, **kwargs):
		pass
	def __len__(self):
		return 0
	def __eq__(self, other):
		return self is other
	def __hash__(self):
		return hash(None)
	def __call__(self, *args, **kwargs):
		return self
	def __trunc__(self):
		return 0
	__sub__ = __div__ = __mul__ = __floordiv__ = __mod__ = __and__ = __or__ = \
	__xor__ = __rsub__ = __rdiv__ = __rmul__ = __rfloordiv__ = __rmod__ = \
	__rand__ = __rxor__ = __ror__ = __radd__ = __pow__ = __rpow__ = \
	__rshift__ = __lshift__ = __rrshift__ = __rlshift__ = __truediv__ = \
	__rtruediv__ = __add__ = __getitem__ = __neg__ = __pos__ = __abs__ = \
	__invert__ = __setattr__ = __delattr__ = __delitem__ = __setitem__ = \
	__iter__ = __call__

Dummy = Dummy()

