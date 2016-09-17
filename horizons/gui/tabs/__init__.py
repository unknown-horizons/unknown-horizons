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

import sys

from .inventorytab import InventoryTab
from .tradetab import TradeTab
from .overviewtab import OverviewTab, GroundUnitOverviewTab, GenericOverviewTab
from .buildingtabs import SignalFireOverviewTab, ResourceDepositOverviewTab, \
						TowerOverviewTab
from .enemybuildingtabs import EnemyBuildingOverviewTab, EnemyWarehouseOverviewTab
from .productiontabs import ProductionOverviewTab, LumberjackOverviewTab, \
						SmallProductionOverviewTab
from .residentialtabs import SettlerOverviewTab
from .shiptabs import ShipOverviewTab, FightingShipOverviewTab, \
						TradeShipOverviewTab, TraderShipOverviewTab, \
                                                EnemyShipOverviewTab
from .buyselltab import BuySellTab
from .buildtabs import BuildTab
from .tabwidget import TabWidget
from .boatbuildertabs import ProducerOverviewTabBase, UnitbuilderTabBase, BoatbuilderTab, \
                                                BoatbuilderFisherTab, BoatbuilderTradeTab, \
                                                BoatbuilderWar1Tab, BoatbuilderWar2Tab, \
                                                BoatbuilderConfirmTab
from .mainsquaretabs import AccountTab, MainSquareOverviewTab, \
						MainSquareSailorsTab, MainSquarePioneersTab, \
						MainSquareSettlersTab, MainSquareCitizensTab
from .buildrelatedtab import BuildRelatedTab

from .diplomacytab import DiplomacyTab
from .selectmultitab import SelectMultiTab

from .barrackstabs import BarracksTab, BarracksSelectTab, \
						BarracksSwordmanTab, BarracksConfirmTab

def resolve_tab(tabclass_name):
	"""Converts a string like 'DiplomacyTab' to the respective class DiplomacyTab."""
	return getattr(sys.modules[__name__], tabclass_name)
