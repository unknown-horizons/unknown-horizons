# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from horizons.util.python import decorators


class DifficultySettings(object):
    EASY_LEVEL = 0
    DEFAULT_LEVEL = 1

    levels = {}

    @classmethod
    def get_settings(cls, level):
        if level not in cls.levels:
            return None
        return cls.levels[level](level)

    @classmethod
    def register_levels(cls):
        cls.levels[cls.EASY_LEVEL] = EasySettings
        cls.levels[cls.DEFAULT_LEVEL] = DefaultSettings


class DifficultyClass(object):
    def __init__(self, level):
        self.level = level


class DefaultSettings(DifficultyClass):
    extra_happiness_constant = 0
    happiness_multiplier = 1
    tax_multiplier = 1


class EasySettings(DefaultSettings):
    tax_multiplier = 1.5

DifficultySettings.register_levels()

decorators.bind_all(DifficultySettings)
decorators.bind_all(DifficultyClass)
decorators.bind_all(DefaultSettings)
decorators.bind_all(EasySettings)
