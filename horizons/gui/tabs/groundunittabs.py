from horizons.gui.tabs import OverviewTab, TradeTab
from horizons.i18n import _lazy

class GroundUnitOverviewTab(OverviewTab):
	widget = 'overview_war_groundunit.xml'
	helptext = _lazy("Groundunit overview")

	def init_widget(self):
		super(GroundUnitOverviewTab, self).init_widget()