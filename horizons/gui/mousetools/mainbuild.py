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

from fife import fife
import logging
import random
import weakref

import horizons.globals

from horizons.entities import Entities
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.python import decorators
from horizons.util.shapes import Point
from horizons.util.worldobject import WorldObject
from horizons.command.building import Build
from horizons.component.selectablecomponent import SelectableBuildingComponent, SelectableComponent
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.command.sounds import PlaySound
from horizons.gui.util import load_uh_widget
from horizons.constants import BUILDINGS, GFX
from horizons.extscheduler import ExtScheduler
from horizons.messaging import SettlementRangeChanged, WorldObjectDeleted, SettlementInventoryUpdated, PlayerInventoryUpdated

import buildingtool
import buildinglogic

decorators.bind_all(BuildingTool)
decorators.bind_all(SettlementBuildingToolLogic)
decorators.bind_all(ShipBuildingToolLogic)
decorators.bind_all(BuildRelatedBuildingToolLogic)