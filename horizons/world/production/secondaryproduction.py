# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from primaryproduction import PrimaryProduction
from horizons.world.consumer import Consumer
from horizons.gui.tabs import TabWidget, ProductionOverviewTab, InventoryTab

class SecondaryProduction(Consumer, PrimaryProduction):
	"""Represents a producer, that consumes ressources for production of other ressources
	(e.g. blacksmith).

	TUTORIAL:
	As you may notice through the detailed distinction of Consumer and Producer classes, it's now
	very simple to create new classes with the wanted behavior. You will notice that we love this
	way of doing things and tend to abstract as much as possible.

	By now you should have a fair overview of how Unknown Horizons works. The tutorial ends here. From now
	you might want to take a look into the horizons/gui and horizons/util folders to checkout the workings
	of the gui and some extra stuff we use. Since you came all the way here, you are now ready to
	get your hands dirty and start working. So check out the bugtracker at www.unknown-horizons.org/trac/
	and see if there's a nice ticket for you :) For further questions just visit us on irc:
	#unknown-horizons @ irc.freenode.net. We'll be happy to answer any questions.

	Have fun with Unknown Horizons!
	"""

	def show_menu(self):
		horizons.main.session.ingame_gui.show_menu(TabWidget(tabs= [ProductionOverviewTab(self), InventoryTab(self)]))
