#!/usr/bin/python


import getopt
import os
import sys
import platform
import signal
import logging
import logging.config
import logging.handlers
import gettext
gettext.install('', unicode=True)

sys.path.append(os.getcwd())
from horizons.network.client import Client, ClientMode
import horizons.network

#-------------------------------------------------------------------------------

class AlarmException(Exception):
  pass

def alarmhandler(signum, frame):
  raise AlarmException

def nbrawinput(prompt = '', timeout = 1):
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
  print "Usage: %s -h host -p port" % (sys.argv[0])

def onquit(*args):
  try:
    client.disconnect()
  except horizons.network.NetworkException, e:
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
  if len(games) > 0:
    print "[GAMESLIST]"
    for game in games:
      print "  [%s] map=%s maxplayers=%d playercnt=%d" % (game.uuid, game.mapname, game.maxplayers, game.playercnt)
  else:
    print "No games available"

def oncreate(*args):
  global client
  if len(args) != 2:
    print "Syntax: create <mapname> <maxplayers>"
    return
  try:
    maxplayers = int(args[1])
    game = client.creategame(args[0], maxplayers)
    print "[GAME] [%s] mapname=%s maxplayers=%d playercnt=%d" % (game.uuid, game.mapname, game.maxplayers, game.playercnt)
    for player in game.players:
      print "  Player: %s (%s)" % (player.name, player.address)
  except ValueError, IndexError:
    print "Maxplayers must be an integer"

def onjoin(*args):
  global client
  if len(args) != 1:
    print "Syntax: join <uuid>"
    return
  try:
    game = client.joingame(args[0])
    print "[GAME] [%s] mapname=%s maxplayers=%d playercnt=%d" % (game.uuid, game.mapname, game.maxplayers, game.playercnt)
    for player in game.players:
      print "  Player: %s (%s)" % (player.name, player.address)
  except ValueError:
    print "Invalid UUID"

def onleave(*args):
  global client
  client.leavegame()

def onchat(*args):
  global client
  client.chat(' '.join(args))

def cb_onchat(game, player, msg):
  global client
  print "[CHAT] [%s] %s: %s" % (game.uuid, player, msg)

def cb_onjoin(game, player):
  global client
  print "[JOIN] [%s] %s joins" % (game.uuid, player)

def cb_onleave(game, player):
  global client
  print "[LEAVE] [%s] %s leaves" % (game.uuid, player)

def cb_onp2pdata(address, data):
  global client
  print "[P2P DATA] %s: %s" % (address, data)

def cb_ongamestart(game):
  global client
  print "[GAMESTART]"

def onauto(*args):
  global client
  mapname = "autocreated"
  maxplayers = 4
  if len(args) >= 1:
    mapname = args[0]
  if len(args) >= 2:
    try:
      maxplayers = int(args[1])
    except ValueError, IndexError:
      print "Maxplayers must be an integer"
      return
  client.connect()
  games = client.listgames(mapname, maxplayers)
  if len(games) > 0:
    game = client.joingame(games[0].uuid)
  else:
    game = client.creategame(mapname, maxplayers)
  print "[GAME] [%s] mapname=%s maxplayers=%d playercnt=%d" % (game.uuid, game.mapname, game.maxplayers, game.playercnt)
  for player in game.players:
    print "  Player: %s (%s)" % (player.name, player.address)
  client.chat("I am here guys. Game can start")

def onp2psend(*args):
  global client
  if client.mode is not ClientMode.Peer2Peer:
    print "[ERROR] Client not in peer 2 peer mode"
    return
  client.send(' '.join(args))

def onname(*args):
  global name
  print "[NAME] My name is %s" % (name)

def onstatus(*args):
  global name, client
  statusstr = "[STATUS]"
  statusstr += " name=%s" % (name)
  statusstr += " mode=%s" % ("P2P" if client.mode is ClientMode.Peer2Peer else "Server")
  statusstr += " connected=%s" % ("yes" if client.isconnected() else "no")
  statusstr += " server=%s" % (client.serveraddress if client.mode is ClientMode.Server else "N/A")
  print statusstr
  if client.isconnected():
    if client.game is not None:
      print "[STATUS] game: uuid=%s mapname=%s maxplayers=%d playercnt=%d" % (client.game.uuid, client.game.mapname, client.game.maxplayers, client.game.playercnt)
      for player in client.game.players:
        print "[STATUS]  Player: %s (%s)" % (player.name, player.address)

def onhelp(*args):
  global commands, prompt
  print "Available commands:"
  for command in sorted(commands.iterkeys()):
    print "  %s" % (command)

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
  'p2p':        onp2psend,
  'name':       onname,
  'status':     onstatus,
}
prompt = ">>>"

if platform.system() == "Windows":
  print "Testclient doesn't run on windows"
  sys.exit(1)

try:
  opts, args = getopt.getopt(sys.argv[1:], 'h:p:')
except getopt.GetoptError, err:
  print str(err)
  usage()
  sys.exit(1)

try:
  for (key, value) in opts:
    if key == '-h':
      host = value
    if key == '-p':
      port = int(value)
except ValueError, IndexError:
  port = 0

if host == None or port == None or port <= 0:
  usage()
  sys.exit(1)

logging.config.fileConfig( os.path.join('content', 'logging.conf'))
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logging.getLogger("network").setLevel(logging.DEBUG)

version = "0.512a"
name = "client-%u" % (os.getpid())
onname(name)
client = Client(name, version, [host, port], None)
client.register_callback("lobbygame_chat", cb_onchat)
client.register_callback("lobbygame_join", cb_onjoin)
client.register_callback("lobbygame_leave", cb_onleave)
client.register_callback("lobbygame_starts", cb_ongamestart)
client.register_callback("p2p_data", cb_onp2pdata)

print prompt,
while True:
  try:
    if client.isconnected():
      client.ping()

    text = nbrawinput()
    if text is None:
      continue

    pieces = filter(lambda x: len(x.strip()) > 0, text.strip().split(' '))
    if len(pieces) <= 0:
      print prompt,
      continue

    cmd = pieces.pop(0)
    if cmd not in commands:
      print "[ERROR] Unknown command"
    else:
      commands[cmd](*pieces)
  except horizons.network.NetworkException, e:
    print "[ERROR] %s" % (e)
  print prompt,
