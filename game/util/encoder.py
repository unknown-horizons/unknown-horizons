def encode(obj, *classes):
	if obj is None:
		return 'n'
	if type(obj) == bool:
		return 'b' + ('t' if obj else 'f')
	if type(obj) == int:
		return 'i' + str(obj)
	if type(obj) == long:
		return 'I' + str(obj)
	if type(obj) == str:
		return 's' + str(len(obj)) + ':' + obj
	if type(obj) == list:
		return 'l' + str(len(obj)) + ''.join(encode(i, *classes) for i in obj)
	if type(obj) == tuple:
		return 't' + str(len(obj)) + ''.join(encode(i, *classes) for i in obj)
	if type(obj) == set:
		return 'z' + str(len(obj)) + ''.join(encode(i, *classes) for i in obj)
	if type(obj) == frozenset:
		return 'f' + str(len(obj)) + ''.join(encode(i, *classes) for i in obj)
	if type(obj) == dict:
		return 'd' + str(len(obj)) + ''.join(encode(i, *classes) + encode(j, *classes) for i, j in obj.items())
	if obj.__class__ in classes:
		attrs = [i for i in dir(obj) if type(i) != str or i[0] != '_']
		return 'o' + encode(obj.__class__.__name__, *classes) + str(len(attrs)) + ':' + ''.join(encode(i, *classes) + encode(getattr(obj,i), *classes) for i in attrs)
	raise NotImplementedError("Cant handle object " + repr(obj.__class__))

def decode(text, *classes):
	return __decode(text, 0, classes)[1]

def __read_number(text, pos):
	for p in xrange(pos, len(text)):
		if text[p] not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') and (p != pos or text[p] not in ('+', '-')):
			return text[pos:p]
	return text[pos:]

def __decode(text, pos, classes):
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
	if text[pos] == 's':
		i = __read_number(text, 1 + pos)
		return (2 + len(i) + int(i), text[2 + len(i) + pos:2 + len(i) + int(i) + pos])
	if text[pos] in ('l', 't'):
		i = __read_number(text, 1 + pos)
		length = 1 + len(i)
		r = []
		for x in xrange(0, int(i)):
			l, o = __decode(text, pos + length, classes)
			length += l
			r.append(o)
		return (length, tuple(r) if text[pos] == 't' else r)
	if text[pos] in ('z', 'f'):
		i = __read_number(text, 1 + pos)
		length = 1 + len(i)
		r = set()
		for x in xrange(0, int(i)):
			l, o = __decode(text, pos + length, classes)
			length += l
			r.add(o)
		return (length, frozenset(r) if text[pos] == 'f' else r)
	if text[pos] == 'd':
		i = __read_number(text, 1 + pos)
		length = 1 + len(i)
		r = {}
		for x in xrange(0, int(i)):
			l, k = __decode(text, pos + length, classes)
			length += l
			l, v = __decode(text, pos + length, classes)
			length += l
			r[k] = v
		return (length, r)
	if text[pos] == 'o':
		length, class_name = __decode(text, pos + 1, classes)
		i = __read_number(text, 1 + length + pos)
		length += 1 + len(i)
		for c in classes:
			if c.__name__ == class_name:
				r = c.__new__(c)
				for x in xrange(0, int(i)):
					l, k = __decode(text, pos + length, classes)
					length += l
					l, v = __decode(text, pos + length, classes)
					length += l
					setattr(r, k, v)
				return (length, r)
		raise NotImplementedError("Cant handle object " + repr(class_name))
	return (0, None)
