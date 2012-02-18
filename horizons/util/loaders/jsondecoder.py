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

import json

class JsonDecoder:
	@classmethod
	def load(cls, path):
		def _decode_list(lst):
			newlist = []
			for i in lst:
				if isinstance(i, unicode):
					i = i.encode('utf-8')
				elif isinstance(i, list):
					i = _decode_list(i)
				newlist.append(i)
			return newlist

		def _decode_dict(dct):
			newdict = {}
			for k, v in dct.iteritems():
				if isinstance(k, unicode):
					try:
						k = int(k)
					except ValueError:
						k = k.encode('utf-8')
				if isinstance(v, unicode):
					v = v.encode('utf-8')
				elif isinstance(v, list):
					v = _decode_list(v)
				newdict[k] = v
			return newdict

		with open(path, "rb") as f:
			return json.load(f, encoding="ascii", object_hook=_decode_dict)
