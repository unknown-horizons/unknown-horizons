#!/usr/bin/env python3

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


from __future__ import print_function
import getopt
import os
import sys
import platform
import signal
import logging
import logging.config
import logging.handlers

sys.path.append(os.getcwd())
from horizons.network.client import Client, ClientMode
import horizons.network

#-------------------------------------------------------------------------------


class AlarmException(Exception):
	pass


def alarmhandler(signum, frame):
	raise AlarmException


def nbrawinput(prompt='', timeout=1):
	signal.signal(signal.SIGALRM, alarmhandler)
	signal.alarm(timeout)
	try:
		text = raw_input(prompt)
		signal.alarm(0)
		return text
	except AlarmException:
		"""nothing in here"""
	signal.signal(signal.SIGALRM, signal.SIG_IGN)
	return None

#-------------------------------------------------------------------------------


def usage():
	print("Usage: {} -h host -p port".format(sys.argv[0]))


def onquit(*args):
	try:
		client.disconnect()
	except horizons.network.NetworkException:
		"""ignore the errors"""
	sys.exit(0)


def onconnect(*args):
	global client
	client.connect()


def ondisconnect(*args):
	global client
	client.disconnect()


def onlist(*args):
	global client
	games = client.listgames(*args)
	if games:
		print("[GAMESLIST]")
		for game in games:
			print("  [{}] map={} maxplayers={:d} playercnt={:d} name={}"
			      .format(game.uuid, game.mapname, game.maxplayers, game.playercnt, game.name))
	else:
		print("No games available")


def oncreate(*args):
	global client
	if len(args) != 3:
		print("Syntax: create <mapname> <maxplayers> <gamename>")
		return
	try:
		maxplayers = int(args[1])
		game = client.creategame(unicode(args[0]), maxplayers, unicode(args[2]))
		print("[GAME] [{}] mapname={} maxplayers={:d} playercnt={:d}"
		      .format(game.uuid, game.mapname, game.maxplayers, game.playercnt))
		for player in game.players:
			print("  Player: {} ({})".format(player.name, player.sid))
	except (ValueError, IndexError):
		print("Maxplayers must be an integer")


def onjoin(*args):
	global client
	if len(args) != 1:
		print("Syntax: join <uuid>")
		return
	try:
		game = client.joingame(unicode(args[0]))
		print("[GAME] [{}] mapname={} maxplayers={:d} playercnt={:d}"
		      .format(game.uuid, game.mapname, game.maxplayers, game.playercnt))
		for player in game.players:
			print("  Player: {} ({})".format(player.name, player.sid))
	except ValueError:
		print("Invalid UUID")


def onleave(*args):
	global client
	client.leavegame()


def onchat(*args):
	global client
	client.chat(u' '.join(args))


def cb_onchat(game, player, msg):
	print("[ONCHAT] [{}] {}: {}".format(game.uuid, player, msg))


def cb_onjoin(game, player):
	print("[ONJOIN] [{}] {} joins".format(game.uuid, player))


def cb_onleave(game, player):
	print("[ONLEAVE] [{}] {} leaves".format(game.uuid, player))


def cb_onchangename(game, oldplayer, newplayer, myself):
	global name
	print("[ONCHANGENAME] [{}] {} changed name to {}"
	      .format(game.uuid, oldplayer.name, newplayer.name))
	if myself:
		name = newplayer.name
		print("[NAME] My new name is {}".format(name))


def cb_ongameprepare(game):
	print("[ONGAMEPREPARE]")


def cb_ongamestarts(game):
	print("[ONGAMESTART]")


def cb_ongamedata(data):
	print("[ONGAMEDATA]: {}".format(data))


def onauto(*args):
	global client
	mapname = u"autocreated"
	gamename = u"mygame"
	maxplayers = 4
	if len(args) >= 1:
		mapname = unicode(args[0])
	if len(args) >= 2:
		try:
			maxplayers = int(args[1])
		except (ValueError, IndexError):
			print("Maxplayers must be an integer")
			return
	client.connect()
	games = client.listgames(mapname, maxplayers)
	if games:
		game = client.joingame(games[0].uuid)
	else:
		game = client.creategame(mapname, maxplayers, gamename)
	print("[GAME] [{}] mapname={} maxplayers={:d} playercnt={:d}"
	      .format(game.uuid, game.mapname, game.maxplayers, game.playercnt))
	for player in game.players:
		print("  Player: {}".format(player.name))
	client.chat("I am here guys. Game can start")


def ongamedata(*args):
	global client
	if client.mode is not ClientMode.Game:
		print("[ERROR] Client not in game mode")
		return
	client.send(u' '.join(args))


def onname(*args):
	global name, client
	if len(args) == 1:
		# see documentation for client.changename() why this code is like that
		if not client.changename(unicode(args[0])):
			return
		name = unicode(args[0])
	print("[NAME] My name is {}".format(name))


def onstatus(*args):
	global name, client
	statusstr = "[STATUS] name={} mode={}".format(name, "GAME" if client.mode is ClientMode.Game else "Server")
	statusstr += " connected={}".format("yes" if client.isconnected() else "no")
	statusstr += " server={}".format(client.serveraddress)
	print(statusstr)
	if client.isconnected():
		if client.game is not None:
			print("[STATUS] game: uuid={} mapname={} maxplayers={:d} playercnt={:d}"
			      .format(client.game.uuid, client.game.mapname, client.game.maxplayers, client.game.playercnt))
		for player in client.game.players:
			print("[STATUS]  Player: {}".format(player.name))


def onhelp(*args):
	global commands, prompt
	print("Available commands:")
	for command in sorted(commands.iterkeys()):
		print("  {}".format(command))

#-------------------------------------------------------------------------------


host = None
port = 0
commands = {
	'help':       onhelp,
	'connect':    onconnect,
	'disconnect': ondisconnect,
	'list':       onlist,
	'create':     oncreate,
	'join':       onjoin,
	'leave':      onleave,
	'chat':       onchat,
	'quit':       onquit,
	'auto':       onauto,
	'gamedata':   ongamedata,
	'name':       onname,
	'status':     onstatus,
}
prompt = ">>>"

if platform.system() == "Windows":
	print("Testclient doesn't run on windows")
	sys.exit(1)

try:
	opts, args = getopt.getopt(sys.argv[1:], 'h:p:')
except getopt.GetoptError as err:
	print(str(err))
	usage()
	sys.exit(1)

try:
	for (key, value) in opts:
		if key == '-h':
			host = value
		if key == '-p':
			port = int(value)
except (ValueError, IndexError):
	port = 0

if host is None or port is None or port <= 0:
	usage()
	sys.exit(1)

logging.config.fileConfig(os.path.join('content', 'logging.conf'))
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logging.getLogger("network").setLevel(logging.DEBUG)

client = None
version = u"0.512a"
name = u"client-{}".format(os.getpid())
onname()
client = Client(name, version, [host, port], None)
client.register_callback("lobbygame_chat", cb_onchat)
client.register_callback("lobbygame_join", cb_onjoin)
client.register_callback("lobbygame_leave", cb_onleave)
client.register_callback("lobbygame_changename", cb_onchangename)
client.register_callback("lobbygame_starts", cb_ongameprepare)
client.register_callback("game_starts", cb_ongamestarts)
client.register_callback("game_data", cb_ongamedata)

print(prompt, end=' ')
while True:
	try:
		if client.isconnected():
			client.ping()

		text = nbrawinput()
		if text is None:
			continue

		pieces = filter(lambda x: len(x.strip()) > 0, text.strip().split(' '))
		if len(pieces) <= 0:
			print(prompt, end=' ')
			continue

		cmd = pieces.pop(0)
		if cmd not in commands:
			print("[ERROR] Unknown command")
		else:
			commands[cmd](*pieces)
	except horizons.network.NetworkException as e:
		print("[ERROR] {}".format(e))
	print(prompt, end=' ')
