# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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

classes=[]

def register_classes(*classes_):
	global classes
	for c in classes_:
		classes.append(c)

def encode(obj):
	if obj is None:
		return 'n'
	if type(obj) == bool:
		return 'b' + ('t' if obj else 'f')
	if type(obj) == int:
		return 'i' + str(obj)
	if type(obj) == long:
		return 'I' + str(obj)
	if type(obj) == float:
		return 'f' + str(obj)
	if type(obj) == str:
		return 's' + str(len(obj)) + ':' + obj
	if type(obj) == list:
		return 'l' + str(len(obj)) + ''.join(encode(i) for i in obj)
	if type(obj) == tuple:
		return 't' + str(len(obj)) + ''.join(encode(i) for i in obj)
	if type(obj) == set:
		return 'z' + str(len(obj)) + ''.join(encode(i) for i in obj)
	if type(obj) == frozenset:
		return 'Z' + str(len(obj)) + ''.join(encode(i) for i in obj)
	if type(obj) == dict:
		return 'd' + str(len(obj)) + ''.join(encode(i) + encode(j) for i, j in obj.items())
	if obj.__class__ in classes:
		attrs = [i for i in dir(obj) if type(i) != str or i[0] != '_']
		return 'o' + encode(obj.__class__.__name__) + str(len(attrs)) + ''.join(encode(i) + encode(getattr(obj,i)) for i in attrs)
	raise NotImplementedError("Cant handle object " + repr(obj.__class__))

def decode(text):
	return __decode(text, 0)[1]

def __read_number(text, pos):
	for p in xrange(pos, len(text)):
		if text[p] not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.') and (p != pos or text[p] not in ('+', '-')):
			return text[pos:p]
	return text[pos:]

def __decode(text, pos):
	if text[pos] == 'n':
		return (1, None)
	if text[pos] == 'b':
		return (2, text[1 + pos] == 't')
	if text[pos] == 'i':
		i = __read_number(text, 1 + pos)
		return (1 + len(i), int(i))
	if text[pos] == 'I':
		i = __read_number(text, 1 + pos)
		return (1 + len(i), long(i))
	if text[pos] == 'f':
		i = __read_number(text, 1 + pos)
		return (1 + len(i), float(i))
	if text[pos] == 's':
		i = __read_number(text, 1 + pos)
		return (2 + len(i) + int(i), text[2 + len(i) + pos:2 + len(i) + int(i) + pos])
	if text[pos] in ('l', 't'):
		i = __read_number(text, 1 + pos)
		length = 1 + len(i)
		r = []
		for x in xrange(0, int(i)):
			l, o = __decode(text, pos + length)
			length += l
			r.append(o)
		return (length, tuple(r) if text[pos] == 't' else r)
	if text[pos] in ('z', 'Z'):
		i = __read_number(text, 1 + pos)
		length = 1 + len(i)
		r = set()
		for x in xrange(0, int(i)):
			l, o = __decode(text, pos + length)
			length += l
			r.add(o)
		return (length, frozenset(r) if text[pos] == 'f' else r)
	if text[pos] == 'd':
		i = __read_number(text, 1 + pos)
		length = 1 + len(i)
		r = {}
		for x in xrange(0, int(i)):
			l, k = __decode(text, pos + length)
			length += l
			l, v = __decode(text, pos + length)
			length += l
			r[k] = v
		return (length, r)
	if text[pos] == 'o':
		length, class_name = __decode(text, pos + 1)
		i = __read_number(text, 1 + length + pos)
		length += 1 + len(i)
		for c in classes:
			if c.__name__ == class_name:
				r = c.__new__(c)
				for x in xrange(0, int(i)):
					l, k = __decode(text, pos + length)
					length += l
					l, v = __decode(text, pos + length)
					length += l
					setattr(r, k, v)
				return (length, r)
		raise NotImplementedError("Cant handle object " + repr(class_name))
	return (0, None)
