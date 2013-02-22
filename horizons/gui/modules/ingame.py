# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

import horizons.globals
from horizons.command.misc import Chat
from horizons.command.uioptions import RenameObject
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.component.namedcomponent import NamedComponent, SettlementNameComponent
from horizons.constants import GUI
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.gui.windows import Dialog, Window
from horizons.messaging import SettlerInhabitantsChanged, HoverSettlementChanged, ResourceBarResize
from horizons.util.pychanchildfinder import PychanChildFinder
from horizons.util.python.callback import Callback


class ChatDialog(Window):
	"""Allow player to send messages to other players."""

	def __init__(self, windows, session):
		super(ChatDialog, self).__init__(windows)

		self._session = session
		self._widget = load_uh_widget('chat.xml')

		events = {
			OkButton.DEFAULT_NAME: self._do_chat,
			CancelButton.DEFAULT_NAME: self._windows.close
		}
		self._widget.mapEvents(events)

		def forward_escape(event):
			# the textfield will eat everything, even control events
			if event.getKey().getValue() == fife.Key.ESCAPE:
				self._windows.close()

		self._widget.findChild(name="msg").capture(forward_escape, "keyPressed")
		self._widget.findChild(name="msg").capture(self._do_chat)

	def show(self):
		self._widget.show()
		self._widget.findChild(name="msg").requestFocus()

	def hide(self):
		self._widget.hide()

	def _do_chat(self):
		"""Actually initiates chatting and hides the dialog"""
		msg = self._widget.findChild(name="msg").text
		Chat(msg).execute(self._session)
		self._widget.findChild(name="msg").text = u''
		self._windows.close()


class ChangeNameDialog(Dialog):
	"""Shows a dialog where the user can change the name of a NamedComponent."""
	modal = True
	focus = 'new_name'

	def __init__(self, windows, session):
		super(ChangeNameDialog, self).__init__(windows)
		self._session = session

	def prepare(self, instance):
		self._gui = load_uh_widget('change_name.xml')

		self._gui.findChild(name="new_name").capture(self._on_keypress, "keyPressed")
		self.return_events = {
			OkButton.DEFAULT_NAME: instance,
			CancelButton.DEFAULT_NAME: False,
		}
		oldname = self._gui.findChild(name='old_name')
		oldname.text = instance.get_component(NamedComponent).name

	def act(self, named_instance):
		"""Renames the instance that is returned by the dialog, if confirmed.

		Hitting Esc or the Cancel button will not trigger a rename.
		if no name was entered or the new name only consists of spaces, abort
		the renaming as well.
		"""
		if not named_instance:
			return

		new_name = self._gui.collectData('new_name')
		self._gui.findChild(name='new_name').text = u''

		if new_name and not new_name.isspace():
			# different namedcomponent classes share the name
			namedcomp = named_instance.get_component_by_name(NamedComponent.NAME)
			RenameObject(namedcomp, new_name).execute(self._session)


class CityInfo(object):
	"""Display city name and inhabitant count at top of the screen."""
	# FIXME updating the position of this widget should be the responsibility of the
	# FIXME ingamegui, as it needs to take the resource overview bar into account as
	# FIXME well. However, an update to the settlement's name triggers repositioning
	# FIXME too, and we'd need a clean way to pass that info the ingamegui.

	def __init__(self, ingame_gui):
		self._ingame_gui = ingame_gui
		self._widget = load_uh_widget('city_info.xml', 'resource_bar')
		self._child_finder = PychanChildFinder(self._widget)

		self._settlement = None
		HoverSettlementChanged.subscribe(self._on_hover_settlement_change)
		SettlerInhabitantsChanged.subscribe(self._on_settler_inhabitant_change)
		ResourceBarResize.subscribe(self._on_resourcebar_resize)

	def end(self):
		HoverSettlementChanged.unsubscribe(self._on_hover_settlement_change)
		SettlerInhabitantsChanged.unsubscribe(self._on_settler_inhabitant_change)
		ResourceBarResize.unsubscribe(self._on_resourcebar_resize)

	def _on_hover_settlement_change(self, message):
		self.set_settlement(message.settlement)

	def set_settlement(self, settlement):
		"""Sets the city name at top center of screen.

		Show/Hide is handled automatically
		"""
		old_was_player_settlement = False
		if self._settlement:
			self._settlement.remove_change_listener(self._update_settlement)
			old_was_player_settlement = self._settlement.owner.is_local_player

		self._settlement = settlement

		if not settlement:
			# we want to hide the widget now (but perhaps delayed).
			if old_was_player_settlement:
				# After scrolling away from settlement, leave name on screen for some
				# seconds. Players can still click on it to rename the settlement now.
				ExtScheduler().add_new_object(self.hide, self,
				      run_in=GUI.CITYINFO_UPDATE_DELAY)
				#TODO 'click to rename' tooltip of cityinfo can stay visible in
				# certain cases if cityinfo gets hidden in tooltip delay buffer.
			else:
				# hovered settlement of other player, simply hide the widget
				self.hide()

		else:
			# do not hide if settlement is hovered and a hide was previously scheduled
			ExtScheduler().rem_call(self, self.hide)

			self._update_settlement() # calls show()
			settlement.add_change_listener(self._update_settlement)

	def _on_settler_inhabitant_change(self, message):
		"""Update display of inhabitants count."""
		foundlabel = self._child_finder('city_inhabitants')
		old_amount = int(foundlabel.text) if foundlabel.text else 0
		foundlabel.text = u' {amount:>4d}'.format(amount=old_amount + message.change)
		foundlabel.resizeToContent()

	def _update_settlement(self):
		city_name_label = self._child_finder('city_name')
		if self._settlement.owner.is_local_player: # allow name changes
			# Update settlement on the resource overview to make sure it
			# is setup correctly for the coming calculations
			self._ingame_gui.resource_overview.set_inventory_instance(self._settlement)
			cb = Callback(self._ingame_gui.show_change_name_dialog, self._settlement)
			helptext = _("Click to change the name of your settlement")
			city_name_label.enable_cursor_change_on_hover()
		else: # no name changes
			cb = lambda: AmbientSoundComponent.play_special('error')
			helptext = u""
			city_name_label.disable_cursor_change_on_hover()

		self._widget.mapEvents({
			'city_name': cb
		})
		city_name_label.helptext = helptext

		foundlabel = self._child_finder('owner_emblem')
		foundlabel.image = 'content/gui/images/tabwidget/emblems/emblem_%s.png' % (self._settlement.owner.color.name)
		foundlabel.helptext = self._settlement.owner.name

		foundlabel = self._child_finder('city_name')
		foundlabel.text = self._settlement.get_component(SettlementNameComponent).name
		foundlabel.resizeToContent()

		foundlabel = self._child_finder('city_inhabitants')
		foundlabel.text = u' {amount:>4d}'.format(amount=self._settlement.inhabitants)
		foundlabel.resizeToContent()

		self._update_position()

	def _update_position(self):
		"""Places cityinfo widget depending on resource bar dimensions.

		For a normal-sized resource bar and reasonably large resolution:
		* determine resource bar length (includes gold)
		* determine empty horizontal space between resbar end and minimap start
		* display cityinfo centered in that area if it is sufficiently large

		If too close to the minimap (cityinfo larger than length of this empty space)
		move cityinfo centered to very upper screen edge. Looks bad, works usually.
		In this case, the resbar is redrawn to put the cityinfo "behind" it visually.
		"""
		width = horizons.globals.fife.engine_settings.getScreenWidth()
		resbar = self._ingame_gui.resource_overview.get_size()
		is_foreign = (self._settlement.owner != self._ingame_gui.session.world.player)
		blocked = self._widget.size[0] + int(1.5 * self._ingame_gui.minimap.get_size()[1])
		# minimap[1] returns width! Use 1.5*width because of the GUI around it

		if is_foreign: # other player, no resbar exists
			self._widget.pos = ('center', 'top')
			xoff = 0
			yoff = 19
		elif blocked < width < resbar[0] + blocked: # large resbar / small resolution
			self._widget.pos = ('center', 'top')
			xoff = 0
			yoff = resbar[1] # below resbar
		else:
			self._widget.pos = ('left', 'top')
			xoff = resbar[0] + (width - blocked - resbar[0]) // 2
			yoff = 24

		self._widget.offset = (xoff, yoff)
		self._widget.position_technique = "{pos[0]}{off[0]:+d}:{pos[1]}{off[1]:+d}".format(
				pos=self._widget.pos,
				off=self._widget.offset)
		self._widget.hide()
		self._widget.show()

	def _on_resourcebar_resize(self, message):
		self._update_position()

	def hide(self):
		self._widget.hide()
