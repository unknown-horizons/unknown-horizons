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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

'''
Warning:
	A Singleton is to some extent the OOP-version of a global variable.
	The Singleton pattern has many downsides.
	Please make sure that this is really the best solution before using this code!
'''

from typing import Any


class Singleton(type):
	"""Traditional Singleton design pattern.

	USAGE:
	class MyClass(metaclass=Singleton):
		pass
	"""
	def __init__(cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> None:
		super().__init__(name, bases, dct)
		cls.instance: Any | None = None

	def __call__(cls, *args: Any, **kwargs: Any) -> Any:
		if cls.instance is None:
			cls.instance = super().__call__(*args, **kwargs)
		return cls.instance

	def destroy_instance(cls) -> None:
		cls.instance = None


class ManualConstructionSingleton(Singleton):
	"""Same as Singleton, but Class() never creates an instance.
	Only create_instance() does."""
	def __call__(cls) -> Any:
		return cls.instance

	def create_instance(cls, *args: Any, **kwargs: Any) -> Any:
		cls.instance = super().__call__(*args, **kwargs)
