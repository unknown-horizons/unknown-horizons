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

import hashlib
import textwrap

from fife.extensions.pychan.widgets import HBox, Label, TextField

import horizons.main
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.constants import MULTIPLAYER
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.icongroup import hr as HRule
from horizons.gui.widgets.imagebutton import CancelButton, OkButton
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.windows import Popup, Window
from horizons.i18n import gettext as T
from horizons.network import enet
from horizons.network.common import ErrorType
from horizons.network.networkinterface import NetworkInterface
from horizons.savegamemanager import SavegameManager
from horizons.util.color import Color
from horizons.util.python.callback import Callback
from horizons.world import load_raw_world

from .playerdataselection import PlayerDataSelection


class MultiplayerMenu(Window):

	def __init__(self, mainmenu, windows):
		super(MultiplayerMenu, self).__init__(windows)
		self._mainmenu = mainmenu
		self._gui = load_uh_widget('multiplayermenu.xml')
		self._gui.mapEvents({
			'cancel' : self._windows.close,
			'join'   : self._join_game,
			'create' : self._create_game,
			'refresh': Callback(self._refresh, play_sound=True)
		})

		self._gui.findChild(name='gamelist').capture(self._update_game_details)
		self._playerdata = PlayerDataSelection()
		self._gui.findChild(name="playerdataselectioncontainer").addChild(self._playerdata.get_widget())

		# to track if the menu window is opened or not.
		self._is_open = False

	def hide(self):
		# Save the player-data on hide so that other menus gets updated data
		self._playerdata.save_settings()
		self._gui.hide()
		ExtScheduler().rem_all_classinst_calls(self)

	def show(self):
		if not self._check_connection():
			return

		if not self._refresh():
			self._windows.close()
			return

		if not self._is_open:
			self._is_open = True
			# subscribe "error" when this menu window is firstly opened
			# only unsubscribe if this menu window is closed
			NetworkInterface().subscribe("error", self._on_error)

		# get updated player data
		self._playerdata.update_data()

		self._gui.show()

		# TODO: Remove once loading a game is implemented again
		self._gui.findChild(name='load').parent.hide()

		ExtScheduler().add_new_object(self._refresh, self, run_in=5, loops=-1)

	def close(self):
		# if the window is not open (due to connection errors), just do nothing
		if not self._is_open:
			return

		self.hide()

		NetworkInterface().unsubscribe("error", self._on_error)
		self._is_open = False

		# the window is also closed when a game starts, don't disconnect in that case
		if NetworkInterface().is_connected and not NetworkInterface().is_joined:
			NetworkInterface().disconnect()

	def on_return(self):
		self._join_game()

	def _check_connection(self):
		"""
		Check if all dependencies for multiplayer games are met and we can connect to
		the master server. If any dependency is not met, the window is closed.
		"""
		# It is important to close this window before showing the error popup.
		# Otherwise closing the popup will trigger `show` again, a new attempt
		# to connect is made, which ends up in an endless loop.

		if enet is None:
			self._windows.close()
			headline = T("Unable to find pyenet")
			descr = T('The multiplayer feature requires the library "pyenet", '
			          "which could not be found on your system.")
			advice = T("Linux users: Try to install pyenet through your package manager.")
			self._windows.open_error_popup(headline, descr, advice)
			return False

		if NetworkInterface() is None:
			try:
				NetworkInterface.create_instance()
			except RuntimeError as e:
				self._windows.close()
				headline = T("Failed to initialize networking.")
				descr = T("Network features could not be initialized with the current configuration.")
				advice = T("Check the settings you specified in the network section.")
				self._windows.open_error_popup(headline, descr, advice, unicode(e))
				return False

		if not NetworkInterface().is_connected:
			try:
				NetworkInterface().connect()
			except Exception as err:
				self._windows.close()
				headline = T("Fatal Network Error")
				descr = T("Could not connect to master server.")
				advice = T("Please check your Internet connection. If it is fine, "
				           "it means our master server is temporarily down.")
				self._windows.open_error_popup(headline, descr, advice, unicode(err))
				return False

		if NetworkInterface().is_joined:
			if not NetworkInterface().leavegame():
				self._windows.close()
				return False

		return True

	def _on_error(self, exception, fatal=True):
		"""Error callback"""
		if not fatal:
			self._windows.open_popup(T("Error"), unicode(exception))
		else:
			self._windows.open_popup(T("Fatal Network Error"),
		                             T("Something went wrong with the network:") + u'\n' +
		                             unicode(exception) )
			# FIXME: this shouldn't be necessary, the main menu window is still somewhere
			# in the stack and we just need to get rid of all MP related windows
			self._mainmenu.show_main()

	def _display_game_name(self, game):
		same_version = game.version == NetworkInterface().get_clientversion()
		template = u"{password}{gamename}: {name} ({players}, {limit}){version}"
		return template.format(
			password="(Password!) " if game.has_password else "",
			name=game.map_name,
			gamename=game.name,
			players=game.player_count,
			limit=game.player_limit,
			version=u" " + T("Version differs!") if not same_version else u"")

	def _refresh(self, play_sound=False):
		"""Refresh list of games.

		@param play_sound: whether to play the refresh sound
		@return bool, whether refresh worked
		"""
		if play_sound:
			AmbientSoundComponent.play_special('refresh')

		self._games = NetworkInterface().get_active_games()
		if self._games is None:
			return False

		gamelist = [self._display_game_name(g) for g in self._games]
		self._gui.distributeInitialData({'gamelist': gamelist})
		self._gui.distributeData({'gamelist': 0})
		self._update_game_details()
		return True

	def _update_game_details(self):
		"""Set map name and other misc data in a widget."""
		try:
			index = self._gui.collectData('gamelist')
			game = self._games[index]
		except IndexError:
			return

		self._gui.findChild(name="game_map").text = T("Map: {map_name}").format(map_name=game.map_name)
		self._gui.findChild(name="game_name").text = T("Name: {game_name}").format(game_name=game.name)
		self._gui.findChild(name="game_creator").text = T("Creator: {game_creator}").format(game_creator=game.creator)
		self._gui.findChild(name="game_playersnum").text = T("Players: {player_amount}/{player_limit}").format(
		                           player_amount=game.player_count,
		                           player_limit=game.player_limit)

		vbox_inner = self._gui.findChild(name="game_info")
		vbox_inner.adaptLayout()

	def _join_game(self):
		"""Joins a multiplayer game. Displays lobby for that specific game"""
		try:
			index = self._gui.collectData('gamelist')
			game = self._games[index]
		except IndexError:
			return

		if game.uuid == -1: # -1 signals no game
			AmbientSoundComponent.play_special('error')
			return

		if game.version != NetworkInterface().get_clientversion():
			self._windows.open_popup(T("Wrong version"),
			                          T("The game's version differs from your version. "
			                            "Every player in a multiplayer game must use the same version. "
			                            "This can be fixed by every player updating to the latest version. "
			                            "Game version: {game_version} Your version: {own_version}").format(
			                            game_version=game.version,
			                            own_version=NetworkInterface().get_clientversion()))
			return

		NetworkInterface().change_name(self._playerdata.get_player_name())
		NetworkInterface().change_color(self._playerdata.get_player_color().id)

		if game.password:
			# ask the player for the password
			popup = PasswordInput(self._windows)
			password = self._windows.open(popup)
			if password is None:
				return
			password = hashlib.sha1(password).hexdigest()
			success = NetworkInterface().joingame(game.uuid, password)
			if not success:
				return
		elif not NetworkInterface().joingame(game.uuid, ''):
			return

		window = GameLobby(self._windows)
		self._windows.open(window)

	def _create_game(self):
		NetworkInterface().change_name(self._playerdata.get_player_name())
		NetworkInterface().change_color(self._playerdata.get_player_color().id)
		self._windows.open(CreateGame(self._windows))


class PasswordInput(Popup):
	"""Popup where players enter a password to join multiplayer games."""
	focus = 'password'

	def __init__(self, windows):
		title = T('Password of the game')
		text = T('Enter password:')
		super(PasswordInput, self).__init__(windows, title, text, show_cancel_button=True)

	def prepare(self, **kwargs):
		super(PasswordInput, self).prepare(**kwargs)
		pw = TextField(name='password', fixed_size=(320, 20))
		box = self._gui.findChild(name='message_box')
		box.addChild(pw)

	def act(self, send_password):
		if not send_password:
			return
		return self._gui.collectData("password")


class CreateGame(Window):
	"""Interface for creating a multiplayer game"""

	def __init__(self, windows):
		super(CreateGame, self).__init__(windows)

		self._gui = load_uh_widget('multiplayer_creategame.xml')
		self._gui.mapEvents({
			'cancel': self._windows.close,
			'create': self.act,
		})

		self._files = []
		self._maps_display = []
		self._map_preview = None

	def hide(self):
		self._gui.hide()

	def show(self):
		self._files, self._maps_display = SavegameManager.get_maps()

		self._gui.distributeInitialData({
			'maplist': self._maps_display,
			'playerlimit': range(2, MULTIPLAYER.MAX_PLAYER_COUNT)
		})

		if self._maps_display: # select first entry
			self._gui.distributeData({
				'maplist': 0,
				'playerlimit': 0
			})
			self._update_infos()

		self._gui.findChild(name="maplist").mapEvents({
			'maplist/action': self._update_infos
		})

		gamenametextfield = self._gui.findChild(name='gamename')
		def gamename_clicked():
			if gamenametextfield.text == 'Unnamed Game':
				gamenametextfield.text = ""
		gamenametextfield.capture(gamename_clicked, event_name='mouseClicked')
		self._gui.show()

	def act(self):
		mapindex = self._gui.collectData('maplist')
		mapname = self._maps_display[mapindex]
		maxplayers = self._gui.collectData('playerlimit') + 2 # 1 is the first entry
		gamename = self._gui.collectData('gamename')
		password = self._gui.collectData('password')
		maphash = ""

		password = hashlib.sha1(password).hexdigest() if password != "" else ""
		game = NetworkInterface().creategame(mapname, maxplayers, gamename, maphash, password)
		if game:
			# FIXME When canceling the lobby, I'd like the player to return to the main mp
			# menu, and not see the 'create game' again. We need to close this window, however,
			# this will trigger the display of the main gui, which will part the game in
			# `MultiplayerMenu._check_connection`
			#self._windows.close()
			window = GameLobby(self._windows)
			self._windows.open(window)

	def _update_infos(self):
		index = self._gui.collectData('maplist')
		mapfile = self._files[index]
		number_of_players = SavegameManager.get_recommended_number_of_players(mapfile)

		lbl = self._gui.findChild(name="recommended_number_of_players_lbl")
		lbl.text = T("Recommended number of players: {number}").format(number=number_of_players)

		self._update_map_preview(mapfile)

	def _update_map_preview(self, map_file):
		if self._map_preview:
			self._map_preview.end()

		world = load_raw_world(map_file)
		self._map_preview = Minimap(
			self._gui.findChild(name='map_preview_minimap'),
			session=None,
			view=None,
			world=world,
			targetrenderer=horizons.globals.fife.targetrenderer,
			imagemanager=horizons.globals.fife.imagemanager,
			cam_border=False,
			use_rotation=False,
			tooltip=None,
			on_click=None,
			preview=True)

		self._map_preview.draw()


class GameLobby(Window):
	"""Chat with other players, change name, wait for the game to begin."""

	def __init__(self, windows):
		super(GameLobby, self).__init__(windows)

		self._gui = load_uh_widget('multiplayer_gamelobby.xml')


		self._gui.mapEvents({
			'cancel': self._cancel,
			'ready_btn': self._on_ready_button_pressed,
		})

		NetworkInterface().subscribe("game_prepare", self._prepare_game)

	def _on_ready_button_pressed(self):
		ready_button = self._gui.findChild(name="ready_btn")
		ready_button.toggle()
		ready_label = self._gui.findChild(name="ready_lbl")
		if ready_button.is_active:
			ready_label.text = T("Ready") + ":"
		else:
			ready_label.text = T("Not ready") + ":"
		ready_label.adaptLayout()
		NetworkInterface().toggle_ready()

	def hide(self):
		self._gui.hide()

	def _cancel(self):
		"""When the lobby is cancelled, close the window and leave the game.

		We can't do this in `close`, because the window will be closed when a game starts
		as well, and we don't want to leave the game then.
		"""
		self._windows.close()
		NetworkInterface().leavegame()

	def on_escape(self):
		self._cancel()

	def close(self):
		self.hide()

		NetworkInterface().unsubscribe("lobbygame_chat", self._on_chat_message)
		NetworkInterface().unsubscribe("lobbygame_join", self._on_player_joined)
		NetworkInterface().unsubscribe("lobbygame_leave", self._on_player_left)
		NetworkInterface().unsubscribe("lobbygame_kick", self._on_player_kicked)
		NetworkInterface().unsubscribe("lobbygame_changename", self._on_player_changed_name)
		NetworkInterface().unsubscribe("lobbygame_changecolor", self._on_player_changed_color)
		NetworkInterface().unsubscribe("lobbygame_toggleready", self._on_player_toggled_ready)
		NetworkInterface().unsubscribe("game_details_changed", self._update_game_details)
		NetworkInterface().unsubscribe("game_prepare", self._prepare_game)
		NetworkInterface().unsubscribe("error", self._on_error)

	def open(self):
		textfield = self._gui.findChild(name="chatTextField")
		textfield.capture(self._send_chat_message)
		welcome_string = T("Enter your message")
		def chatfield_clicked():
			if textfield.text == welcome_string:
				textfield.text = ""
		textfield.text = welcome_string
		textfield.capture(chatfield_clicked, event_name="mouseClicked")

		self._update_game_details()

		NetworkInterface().subscribe("lobbygame_chat", self._on_chat_message)
		NetworkInterface().subscribe("lobbygame_join", self._on_player_joined)
		NetworkInterface().subscribe("lobbygame_leave", self._on_player_left)
		NetworkInterface().subscribe("lobbygame_kick", self._on_player_kicked)
		NetworkInterface().subscribe("lobbygame_changename", self._on_player_changed_name)
		NetworkInterface().subscribe("lobbygame_changecolor", self._on_player_changed_color)
		NetworkInterface().subscribe("lobbygame_toggleready", self._on_player_toggled_ready)
		NetworkInterface().subscribe("game_details_changed", self._update_game_details)
		NetworkInterface().subscribe("error", self._on_error)

		self.show()

	def show(self):
		self._gui.show()

	def _on_error(self, error, fatal=True):
		if error.type == ErrorType.TerminateGame:
			# We can't use `_cancel` here, since that calls `leavegame`, which isn't
			# possible since the game was terminated already.
			self._windows.close()

	def _prepare_game(self, game):
		horizons.main.prepare_multiplayer(game)

	def _update_game_details(self):
		"""Set map name and other misc data"""
		game = NetworkInterface().get_game()

		self._gui.findChild(name="game_map").text = T("Map: {map_name}").format(map_name=game.map_name)
		self._gui.findChild(name="game_name").text = T("Name: {game_name}").format(game_name=game.name)
		self._gui.findChild(name="game_creator").text = T("Creator: {game_creator}").format(game_creator=game.creator)
		self._gui.findChild(name="game_playersnum").text = T("Players: {player_amount}/{player_limit}").format(
		                           player_amount=game.player_count,
		                           player_limit=game.player_limit)

		self._update_players_box(game)
		self._gui.findChild(name="game_info").adaptLayout()

	def _update_players_box(self, game):
		"""Updates player list."""
		players_vbox = self._gui.findChild(name="players_vbox")
		players_vbox.removeAllChildren()

		hr = HRule()
		players_vbox.addChild(hr)

		def _add_player_line(player):
			name = player['name']
			pname = Label(name="pname_%s" % name)
			pname.helptext = T("Click here to change your name and/or color")
			pname.text = name
			pname.min_size = pname.max_size = (130, 15)

			if name == NetworkInterface().get_client_name():
				pname.capture(Callback(self._show_change_player_details_popup, game))

			pcolor = Label(name="pcolor_%s" % name, text=u"   ")
			pcolor.helptext = T("Click here to change your name and/or color")
			pcolor.background_color = player['color']
			pcolor.min_size = pcolor.max_size = (15, 15)

			if name == NetworkInterface().get_client_name():
				pcolor.capture(Callback(self._show_change_player_details_popup, game))

			pstatus = Label(name="pstatus_%s" % name)
			pstatus.text = "\t\t\t" + player['status']
			pstatus.min_size = pstatus.max_size = (120, 15)

			picon = HRule(name="picon_%s" % name)

			hbox = HBox()
			hbox.addChildren(pname, pcolor, pstatus)

			if NetworkInterface().get_client_name() == game.creator and name != game.creator:
				pkick = CancelButton(name="pkick_%s" % name)
				pkick.helptext = T("Kick {player}").format(player=name)
				pkick.capture(Callback(NetworkInterface().kick, player['sid']))
				pkick.path = "images/buttons/delete_small"
				pkick.min_size = pkick.max_size = (20, 15)
				hbox.addChild(pkick)

			players_vbox.addChildren(hbox, picon)

		for player in game.get_player_list():
			_add_player_line(player)

		players_vbox.adaptLayout()

	def _show_change_player_details_popup(self, game):
		"""Shows a dialog where the player can change its name and/or color"""

		assigned = [p["color"] for p in NetworkInterface().get_game().get_player_list()
		            if p["name"] != NetworkInterface().get_client_name()]
		unused_colors = set(Color.get_defaults()) - set(assigned)

		playerdata = PlayerDataSelection(color_palette=unused_colors)
		playerdata.set_player_name(NetworkInterface().get_client_name())
		playerdata.set_color(NetworkInterface().get_client_color())

		dialog = load_uh_widget('set_player_details.xml')
		dialog.findChild(name="playerdataselectioncontainer").addChild(playerdata.get_widget())

		def _change_playerdata():
			NetworkInterface().change_name(playerdata.get_player_name())
			NetworkInterface().change_color(playerdata.get_player_color().id)
			dialog.hide()
			self._update_game_details()

		def _cancel():
			dialog.hide()

		dialog.mapEvents({
			OkButton.DEFAULT_NAME: _change_playerdata,
			CancelButton.DEFAULT_NAME: _cancel
		})

		dialog.show()

	# Functions for handling events on the left side (chat)

	def _send_chat_message(self):
		"""Sends a chat message. Called when user presses enter in the input field"""
		msg = self._gui.findChild(name="chatTextField").text
		if msg:
			self._gui.findChild(name="chatTextField").text = u""
			NetworkInterface().chat(msg)

	def _print_event(self, msg, wrap="*"):
		line_max_length = 40
		if wrap:
			msg = "%s %s %s" % (wrap, msg, wrap)

		lines = textwrap.wrap(msg, line_max_length)

		chatbox = self._gui.findChild(name="chatbox")
		chatbox.items.extend(lines)
		chatbox.selected = len(chatbox.items) - 1

	def _on_chat_message(self, game, player, msg):
		self._print_event(player + ": " + msg, wrap="")

	def _on_player_joined(self, game, player):
		self._print_event(T("{player} has joined the game").format(player=player.name))

	def _on_player_left(self, game, player):
		self._print_event(T("{player} has left the game").format(player=player.name))

	def _on_player_toggled_ready(self, game, plold, plnew, myself):
		self._update_players_box(NetworkInterface().get_game())
		if myself:
			if plnew.ready:
				self._print_event(T("You are now ready"))
			else:
				self._print_event(T("You are not ready anymore"))
		else:
			if plnew.ready:
				self._print_event(T("{player} is now ready").format(player=plnew.name))
			else:
				self._print_event(T("{player} not ready anymore").format(player=plnew.name))

	def _on_player_changed_name(self, game, plold, plnew, myself):
		if myself:
			self._print_event(T("You are now known as {new_name}").format(new_name=plnew.name))
		else:
			self._print_event(T("{player} is now known as {new_name}").format(player=plold.name, new_name=plnew.name))

	def _on_player_changed_color(self, game, plold, plnew, myself):
		if myself:
			self._print_event(T("You changed your color"))
		else:
			self._print_event(T("{player} changed their color").format(player=plnew.name))

	def _on_player_kicked(self, game, player, myself):
		if myself:
			self._windows.open_popup(T("Kicked"), T("You have been kicked from the game by creator"))
			self._windows.close()
		else:
			self._print_event(T("{player} got kicked by creator").format(player=player.name))
