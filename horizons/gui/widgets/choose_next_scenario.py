from horizons.util.gui import load_uh_widget
from horizons.util import Callback
from horizons.extscheduler import ExtScheduler
from horizons.savegamemanager import SavegameManager

class ScenarioChooser(object):
	"""An UI to choose next scenario in a campaign after
	winning the current one.
	"""
	def __init__(self, session):
		self.session = session # We will need that to load scenarios
		self.selected_scenario = None
		self._init_gui()

	def _init_gui(self):
		"""Initial init of gui."""
		self._gui = load_uh_widget("choose_next_scenario.xml")
		self._gui.mapEvents({
		  'choose_scenario' : Callback(self.validate_choice),
		  'cancelButton' : Callback(self.hide),
		  })
		self._gui.position_technique = "automatic" # "center:center"

		#SavegameManager.get_campaign_info(cls, name = "", file = "")
		self.choose_scenario = self._gui.findChild(name="choose_scenario")

	def validate_choice(self, *args, **kwargs):
		if not self.selected_scenario:
			return
		ExtScheduler().add_new_object(Callback(SavegameManager.load_scenario, self.session.campaign, self.selected_scenario), SavegameManager, run_in=1)

	def show(self):
		# Campaign and scenarios data
		campaign_info = SavegameManager.get_campaign_info(name = self.session.campaign['campaign_name'])
		available_scenarios = SavegameManager.get_available_scenarios()[1] # [0] is the list of xml files, we don't need it
		scenarios = [s for s in campaign_info.get('scenario_names', []) if s in available_scenarios]
		self._gui.distributeInitialData({'scenario_list' : scenarios})
		# select the first one
		self._gui.distributeData({ 'scenario_list' : 0, })
		def _update_infos():
			self.selected_scenario = scenarios[self._gui.collectData("scenario_list")]
			data = SavegameManager.get_scenario_info(name = self.selected_scenario)
			#xgettext:python-format
			text = [_("Difficulty: {difficulty}").format(difficulty=data.get('difficulty', '')),
			        _("Author: {author}").format(author=data.get('author', '')),
			        _("Description: {desc}").format(desc=data.get('description', '')),
			       ]
			self._gui.findChild(name="scenario_details").text = u"\n".join(text)
		self._gui.findChild(name="scenario_list").mapEvents({
		  'scenario_list/action': _update_infos,
		  'scenario_list/mouseWheelMovedUp'   : _update_infos,
		  'scenario_list/mouseWheelMovedDown' : _update_infos
		})


		_update_infos()
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

