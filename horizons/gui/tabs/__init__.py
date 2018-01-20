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

import sys

from .barrackstabs import BarracksConfirmTab, BarracksSelectTab, BarracksSwordmanTab, BarracksTab
from .barriertab import BarrierOverviewTab
from .boatbuildertabs import (
	BoatbuilderConfirmTab, BoatbuilderFisherTab, BoatbuilderTab, BoatbuilderTradeTab,
	BoatbuilderWar1Tab, BoatbuilderWar2Tab, ProducerOverviewTabBase, UnitbuilderTabBase)
from .buildingtabs import ResourceDepositOverviewTab, SignalFireOverviewTab, TowerOverviewTab
from .buildrelatedtab import BuildRelatedTab
from .buildtabs import BuildTab
from .buyselltab import BuySellTab
from .diplomacytab import DiplomacyTab
from .enemybuildingtabs import EnemyBuildingOverviewTab, EnemyWarehouseOverviewTab
from .inventorytab import InventoryTab
from .mainsquaretabs import (
	AccountTab, MainSquareCitizensTab, MainSquareMerchantsTab, MainSquareOverviewTab,
	MainSquarePioneersTab, MainSquareSailorsTab, MainSquareSettlersTab)
from .overviewtab import GenericOverviewTab, GroundUnitOverviewTab, OverviewTab
from .productiontabs import LumberjackOverviewTab, ProductionOverviewTab, SmallProductionOverviewTab
from .residentialtabs import SettlerOverviewTab
from .selectmultitab import SelectMultiTab
from .shiptabs import (
	EnemyShipOverviewTab, FightingShipOverviewTab, ShipOverviewTab, TraderShipOverviewTab,
	TradeShipOverviewTab)
from .tabwidget import TabWidget
from .tradetab import TradeTab


def resolve_tab(tabclass_name):
	"""Converts a string like 'DiplomacyTab' to the respective class DiplomacyTab."""
	return getattr(sys.modules[__name__], tabclass_name)
