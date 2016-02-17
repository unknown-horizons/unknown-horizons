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

import gettext
import logging
import uuid

from horizons import network
from horizons.i18n import find_available_languages
from horizons.network import packets, enet
from horizons.network.common import Player, Game, ErrorType


if not enet:
    raise Exception("Could not find enet module.")


MAX_PEERS = 4095
CONNECTION_TIMEOUT = 500
# protocols used by uh versions:
# 0 ... 2012.1
# 1 ... >2012.1
PROTOCOLS = [0, 1]

logging.basicConfig(format='[%(asctime)-15s] [%(levelname)s] %(message)s',
    level=logging.DEBUG)


class Server(object):
    def __init__(self, hostname, port, statistic_file=None):
        packets.SafeUnpickler.set_mode(client=False)
        self.host = None
        self.hostname = hostname
        self.port = port
        self.statistic = {
            'file': statistic_file,
            'timestamp': 0,
            'interval': 1 * 60 * 1000,
        }
        self.capabilities = {
            'minplayers': 2,
            'maxplayers': 8,
            # NOTE: this defines the global packet size maximum.
            # there's still a per packet maximum defined in the
            # individual packet classes
            'maxpacketsize': 2 * 1024 * 1024,
        }
        self.callbacks = {
            'onconnect': [self.onconnect],
            'ondisconnect': [self.ondisconnect],
            'onreceive': [self.onreceive],
            packets.cmd_error: [self.onerror],
            packets.cmd_fatalerror: [self.onfatalerror],
            packets.client.cmd_sessionprops: [self.onsessionprops],
            packets.client.cmd_creategame: [self.oncreategame],
            packets.client.cmd_listgames: [self.onlistgames],
            packets.client.cmd_joingame: [self.onjoingame],
            packets.client.cmd_leavegame: [self.onleavegame],
            packets.client.cmd_chatmsg: [self.onchat],
            packets.client.cmd_changename: [self.onchangename],
            packets.client.cmd_changecolor: [self.onchangecolor],
            packets.client.cmd_preparedgame: [self.onpreparedgame],
            packets.client.cmd_toggleready: [self.ontoggleready],
            packets.client.cmd_kickplayer: [self.onkick],
            # TODO packets.client.cmd_fetch_game:     [ self.onfetchgame ],
            # TODO packets.client.savegame_data:      [ self.onsavegamedata ],
            'preparegame': [self.preparegame],
            'startgame': [self.startgame],
            'leavegame': [self.leavegame],
            'deletegame': [self.deletegame],
            'terminategame': [self.terminategame],
            'gamedata': [self.gamedata],
        }
        self.games = []  # list of games
        self.players = {}  # sessionid => Player() dict
        self.i18n = {}  # lang => gettext dict
        self.check_urandom()
        self.setup_i18n()

    def check_urandom(self):
        try:
            import os
            os.urandom(1)
        except NotImplementedError:
            import random
            import time
            random.seed(uuid.getnode() + int(time.time() * 1e3))
            logging.warning("[INIT] Your system doesn't support /dev/urandom")

    # we use the following custom prefixes/functions to distinguish
    # between server side messages (domain=unknown-horizons-server) and
    # client side messages (domain=unknown-horizons):
    #
    # S_(player,  ...)    ... same as _(...)
    # SN_(player, ...)    ... same as N_(...)
    # __(...)             ... noop for extracting the strings
    def gettext(self, player, message):
        return player.gettext.ugettext(message)

    def ngettext(self, player, msgid1, msgid2, n):
        return player.gettext.ungettext(msgid1, msgid2, n)

    def setup_i18n(self):
        domain = 'unknown-horizons-server'
        for lang, dir in find_available_languages(domain).items():
            if len(dir) <= 0:
                continue
            try:
                self.i18n[lang] = gettext.translation(domain, dir, [lang])
            except IOError:
                pass
        import __builtin__
        __builtin__.__dict__['S_'] = self.gettext
        __builtin__.__dict__['SN_'] = self.ngettext
        __builtin__.__dict__['__'] = lambda x: x

    # uuid4() uses /dev/urandom when possible
    def generate_session_id(self):
        return uuid.uuid4().hex

    def register_callback(self, type, callback, prepend=False):
        if type in self.callbacks:
            if prepend:
                self.callbacks[type].insert(0, callback)
            else:
                self.callbacks[type].append(callback)
        else:
            raise TypeError("Unsupported type")

    def call_callbacks(self, type, *args):
        if type not in self.callbacks:
            return
        ret = True
        for callback in self.callbacks[type]:
            tmp = callback(*args)
            if tmp is None:
                tmp = True
            ret &= tmp
        return ret

    def run(self):
        logging.info("Starting up server on %s:%d" % (self.hostname, self.port))
        try:
            self.host = enet.Host(enet.Address(self.hostname, self.port), MAX_PEERS, 0, 0, 0)
        except (IOError, MemoryError) as e:
            # these exceptions do not provide any information.
            raise network.NetworkException("Unable to create network structure: %s" % (e))

        logging.debug("Entering the main loop...")
        while True:
            if self.statistic['file'] is not None:
                if self.statistic['timestamp'] <= 0:
                    self.print_statistic(self.statistic['file'])
                    self.statistic['timestamp'] = self.statistic['interval']
                else:
                    self.statistic['timestamp'] -= CONNECTION_TIMEOUT

            event = self.host.service(CONNECTION_TIMEOUT)
            if event.type == enet.EVENT_TYPE_NONE:
                continue
            elif event.type == enet.EVENT_TYPE_CONNECT:
                self.call_callbacks("onconnect", event)
            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                self.call_callbacks("ondisconnect", event)
            elif event.type == enet.EVENT_TYPE_RECEIVE:
                self.call_callbacks("onreceive", event)
            else:
                logging.warning("Invalid packet (%u)" % (event.type))

    def send(self, peer, packet, channelid=0):
        if self.host is None:
            raise network.NotConnected("Server is not running")

        self.sendraw(peer, packet.serialize(), channelid)

    def sendraw(self, peer, data, channelid=0):
        if self.host is None:
            raise network.NotConnected("Server is not running")

        packet = enet.Packet(data, enet.PACKET_FLAG_RELIABLE)
        peer.send(channelid, packet)
        self.host.flush()

    def disconnect(self, peer, later=True):
        logging.debug("[DISCONNECT] Disconnecting client %s" % (peer.address))
        try:
            if later:
                peer.disconnect_later()
            else:
                peer.disconnect()
        except IOError:
            peer.reset()

    def error(self, player, message, _type=ErrorType.NotSet):
        self._error(player.peer, S_(player, message), _type)

    def _error(self, peer, message, _type=ErrorType.NotSet):
        self.send(peer, packets.cmd_error(message, _type))

    def fatalerror(self, player, message, later=True):
        self._fatalerror(player.peer, S_(player, message), later)

    def _fatalerror(self, peer, message, later=True):
        self.send(peer, packets.cmd_fatalerror(message))
        self.disconnect(peer, later)

    def onconnect(self, event):
        peer = event.peer
        # disable that check as peer.data may be uninitialized which segfaults then
        # if peer.data in self.players:
        # logging.warning("[CONNECT] Already known player %s!" % (peer.address))
        # self._fatalerror(event.peer, "You can't connect more than once")
        # return
        player = Player(event.peer, self.generate_session_id(), event.data)
        logging.debug("[CONNECT] New Client: %s" % (player))

        # store session id inside enet.peer.data
        # NOTE: ALWAYS initialize peer.data
        event.peer.data = player.sid

        if player.protocol not in PROTOCOLS:
            logging.warning("[CONNECT] %s runs old or unsupported protocol" % (player))
            self.fatalerror(player, __("Old or unsupported multiplayer protocol."
                " Please check your game version"))
            return

        # NOTE: copying bytes or int doesn't work here
        self.players[player.sid] = player
        self.send(event.peer, packets.server.cmd_session(player.sid, self.capabilities))

    def ondisconnect(self, event):
        peer = event.peer
        # check need for early disconnects (e.g. old protocol)
        if peer.data not in self.players:
            return
        player = self.players[peer.data]
        logging.debug("[DISCONNECT] %s disconnected" % (player))
        if player.game is not None:
            self.call_callbacks("leavegame", player)
        del self.players[peer.data]

    def onreceive(self, event):
        peer = event.peer
        # logging.debug("[RECEIVE] Got data from %s" % (peer.address))
        # check player is known by server
        if peer.data not in self.players:
            logging.warning("[RECEIVE] Packet from unknown player %s!" % (peer.address))
            self._fatalerror(event.peer, "I don't know you")
            return

        player = self.players[peer.data]

        # check packet size
        if len(event.packet.data) > self.capabilities['maxpacketsize']:
            logging.warning("[RECEIVE] Global packet size exceeded from %s: size=%d"
                % (peer.address, len(event.packet.data)))
            self.fatalerror(player, __("You've exceeded the global packet size.") + " " +
                __("This should never happen. "
                "Please contact us or file a bug report."))
            return

        # shortpath if game is running
        if player.game is not None and player.game.state is Game.State.Running:
            self.call_callbacks('gamedata', player, event.packet.data)
            return

        packet = None
        try:
            packet = packets.unserialize(event.packet.data, True, player.protocol)
        except network.SoftNetworkException as e:
            self.error(player, e.message)
            return
        except network.PacketTooLarge as e:
            logging.warning("[RECEIVE] Per packet size exceeded from %s: %s" % (player, e))
            self.fatalerror(player, __("You've exceeded the per packet size.") + " " +
                __("This should never happen. "
                "Please contact us or file a bug report.") +
                " " + str(e))
            return
        except Exception as e:
            logging.warning("[RECEIVE] Unknown or malformed packet from %s: %s!" % (player, e))
            self.fatalerror(player, __("Unknown or malformed packet. Please check your game version"))
            return

        # session id check
        if packet.sid != player.sid:
            logging.warning("[RECEIVE] Invalid session id for player %s (%s vs %s)!"
                % (peer.address, packet.sid, player.sid))
            self.fatalerror(player, __("Invalid/Unknown session"))
            # this will trigger ondisconnect() for cleanup
            return

        if packet.__class__ not in self.callbacks:
            logging.warning("[RECEIVE] Unhandled network packet from %s - Ignoring!" % (peer.address))
            return
        self.call_callbacks(packet.__class__, player, packet)

    def onerror(self, player, packet):
        # we shouldn't receive any errors from client
        # so ignore them all
        logging.debug("[ERROR] Client Message: %s" % (packet.errorstr))

    def onfatalerror(self, player, packet):
        # we shouldn't receive any fatala errors from client
        # so just disconnect them
        logging.debug("[FATAL] Client Message: %s" % (packet.errorstr))
        self.disconnect(player.peer)

    def onsessionprops(self, player, packet):
        logging.debug("[PROPS] %s" % (player))
        if hasattr(packet, 'lang'):
            if packet.lang in self.i18n:
                player.gettext = self.i18n[packet.lang]
        self.send(player.peer, packets.cmd_ok())

    def oncreategame(self, player, packet):
        if packet.maxplayers < self.capabilities['minplayers']:
            raise network.SoftNetworkException("You can't run a game with less than %d players"
                % (self.capabilities['minplayers']))
        if packet.maxplayers > self.capabilities['maxplayers']:
            raise network.SoftNetworkException("You can't run a game with more than %d players"
                % (self.capabilities['maxplayers']))
        game = Game(packet, player)
        logging.debug("[CREATE] [%s] %s created %s" % (game.uuid, player, game))
        self.games.append(game)
        self.send(player.peer, packets.server.data_gamestate(game))

    def deletegame(self, game):
        logging.debug("[REMOVE] [%s] %s removed" % (game.uuid, game))
        game.clear()
        self.games.remove(game)

    def onlistgames(self, player, packet):
        logging.debug("[LIST]")
        gameslist = packets.server.data_gameslist()
        for _game in self.games:
            if _game.creator.protocol != player.protocol:
                continue
            if not _game.is_open():
                continue
            if _game.is_full():
                continue
            if packet.clientversion != -1 and packet.clientversion != _game.creator.version:
                continue
            if packet.mapname and packet.mapname != _game.mapname:
                continue
            if packet.maxplayers and packet.maxplayers != _game.maxplayers:
                continue
            gameslist.addgame(_game)
        self.send(player.peer, gameslist)

    def __find_game_from_uuid(self, packet):
        game = None
        for _game in self.games:
            if packet.clientversion != _game.creator.version:
                continue
            if packet.uuid != _game.uuid:
                continue
            game = _game
            break
        return game

    def onjoingame(self, player, packet):
        if player.game is not None:
            self.error(player, __("You can't join a game while in another game"))
            return

        game = self.__find_game_from_uuid(packet)
        if game is None:
            self.error(player, __("Unknown game or game is running a different version"))
            return
        if not game.is_open():
            self.error(player, __("Game has already started. No more joining"))
            return
        if game.is_full():
            self.error(player, __("Game is full"))
            return
        if game.has_password() and packet.password != game.password:
            self.error(player, __("Wrong password"))
            return

        # protocol=0
        # assign free color
        if packet.playercolor is None:
            colors = []
            for _player in game.players:
                colors.append(_player.color)
            for color in range(1, len(colors) + 2):
                if color not in colors:
                    break
            packet.playercolor = color

        # make sure player names, colors and clientids are unique
        for _player in game.players:
            if _player.name == packet.playername:
                self.error(player, __("There's already a player with your name inside this game.") + " " +
                    __("Please change your name."))
                return
            if _player.color == packet.playercolor:
                self.error(player, __("There's already a player with your color inside this game.") + " " +
                    __("Please change your color."))
                return
            if _player.clientid == packet.clientid:
                self.error(player, __("There's already a player with your unique player ID inside this game. "
                    "This should never occur."))
                return

        logging.debug("[JOIN] [%s] %s joined %s" % (game.uuid, player, game))
        game.add_player(player, packet)
        for _player in game.players:
            self.send(_player.peer, packets.server.data_gamestate(game))

        if player.protocol == 0:
            if game.is_full():
                self.call_callbacks("preparegame", game)

    def onleavegame(self, player, packet):
        if player.game is None:
            self.error(player, __("You are not inside a game"))
            return
        self.call_callbacks("leavegame", player)
        self.send(player.peer, packets.cmd_ok())

    def leavegame(self, player):
        game = player.game
        # leaving the game if game has already started is a hard error
        if not game.is_open():
            self.call_callbacks('terminategame', game, player)
            return
        logging.debug("[LEAVE] [%s] %s left %s" % (game.uuid, player, game))
        game.remove_player(player)
        if game.is_empty():
            self.call_callbacks('deletegame', game)
            return
        for _player in game.players:
            self.send(_player.peer, packets.server.data_gamestate(game))
        # the creator leaving the game is a hard error too
        if player.protocol >= 1 and player == game.creator:
            self.call_callbacks('terminategame', game, player)
            return

    def terminategame(self, game, player=None):
        logging.debug("[TERMINATE] [%s] (by %s)" % (game.uuid, player if player is not None else None))
        if game.creator.protocol >= 1 and game.is_open():
            # NOTE: works with protocol >= 1
            for _player in game.players:
                self.error(_player, __("The game has been terminated. The creator has left the game."),
                    ErrorType.TerminateGame)
        else:
            for _player in game.players:
                if _player.peer.state == enet.PEER_STATE_CONNECTED:
                    self.fatalerror(_player,
                        __("One player has terminated their game. "
                        "For technical reasons, this currently means the game cannot continue. "
                        "We are very sorry about that."))
        self.call_callbacks('deletegame', game)

    def preparegame(self, game):
        logging.debug("[PREPARE] [%s] Players: %s" % (game.uuid, [unicode(i) for i in game.players]))
        game.state = Game.State.Prepare
        for _player in game.players:
            self.send(_player.peer, packets.server.cmd_preparegame())

    def startgame(self, game):
        logging.debug("[START] [%s] Players: %s" % (game.uuid, [unicode(i) for i in game.players]))
        game.state = Game.State.Running
        for _player in game.players:
            self.send(_player.peer, packets.server.cmd_startgame())

    def onchat(self, player, packet):
        if player.game is None:
            # just ignore if not inside a game
            self.send(player.peer, packets.cmd_ok())
            return
        game = player.game
        # don't send packets to already started games
        if not game.is_open():
            return
        logging.debug("[CHAT] [%s] %s: %s" % (game.uuid, player, packet.chatmsg))
        for _player in game.players:
            self.send(_player.peer, packets.server.cmd_chatmsg(player.name, packet.chatmsg))

    def onchangename(self, player, packet):
        # NOTE: that event _only_ happens inside a lobby
        if player.game is None:
            # just ignore if not inside a game
            self.send(player.peer, packets.cmd_ok())
            return
        # ignore change to existing name
        if player.name == packet.playername:
            return
        game = player.game
        # don't send packets to already started games
        if not game.is_open():
            return

        # make sure player names are unique
        for _player in game.players:
            if _player.name == packet.playername:
                self.error(player, __("There's already a player with your name inside this game.") + " " +
                    __("Unable to change your name."))
                return

        # ACK the change
        logging.debug("[CHANGENAME] [%s] %s -> %s" % (game.uuid, player.name, packet.playername))
        player.name = packet.playername
        for _player in game.players:
            self.send(_player.peer, packets.server.data_gamestate(game))

    def onchangecolor(self, player, packet):
        # NOTE: that event _only_ happens inside a lobby
        if player.game is None:
            # just ignore if not inside a game
            self.send(player.peer, packets.cmd_ok())
            return
        # ignore change to same color
        if player.color == packet.playercolor:
            return
        game = player.game
        # don't send packets to already started games
        if not game.is_open():
            return

        # make sure player colors are unique
        for _player in game.players:
            if _player.color == packet.playercolor:
                self.error(player, __("There's already a player with your color inside this game.") + " " +
                    __("Unable to change your color."))
                return

        # ACK the change
        logging.debug("[CHANGECOLOR] [%s] Player:%s %s -> %s" % (game.uuid, player.name,
            player.color, packet.playercolor))
        player.color = packet.playercolor
        for _player in game.players:
            self.send(_player.peer, packets.server.data_gamestate(game))

    def gamedata(self, player, data):
        game = player.game
        # logging.debug("[GAMEDATA] [%s] %s" % (game.uuid, player))
        for _player in game.players:
            if _player is player:
                continue
            self.sendraw(_player.peer, data)

    # this event happens after a player is done with loading
    # and ready to start the game. we need to wait for all players
    def onpreparedgame(self, player, packet):
        game = player.game
        if game is None:
            return
        logging.debug("[PREPARED] [%s] %s" % (game.uuid, player))
        player.prepared = True
        count = 0
        for _player in game.players:
            if _player.prepared:
                count += 1
        if count != game.playercnt:
            return
        self.call_callbacks('startgame', game)

    def ontoggleready(self, player, packet):
        game = player.game
        if game is None:
            return
        # don't send packets to already started games
        if not game.is_open():
            return

        # ACK the change
        player.toggle_ready()
        logging.debug("[TOGGLEREADY] [%s] Player:%s %s ready" %
                (game.uuid, player.name, "is not" if not player.ready else "is"))
        for _player in game.players:
            self.send(_player.peer, packets.server.data_gamestate(game))

        # start the game after the ACK
        if game.is_ready():
            self.call_callbacks("preparegame", game)

    def onkick(self, player, packet):
        game = player.game
        if game is None:
            return
        # don't send packets to already started games
        if not game.is_open():
            return
        if player is not game.creator:
            return

        kickplayer = None
        for _player in game.players:
            if _player.sid == packet.kicksid:
                kickplayer = _player
                break
        if kickplayer is None:
            return
        if kickplayer is game.creator:
            return

        logging.debug("[KICK] [%s] %s got kicked" % (game.uuid, kickplayer.name))
        for _player in game.players:
            self.send(_player.peer, packets.server.cmd_kickplayer(kickplayer))
        self.call_callbacks("leavegame", kickplayer)

    # TODO fix
    def onfetchgame(self, player, packet):
        game = player.game

        if game is not None:
            self.error(player, __("You can't fetch a game while in another game"))

        fetch_game = self.__find_game_from_uuid(packet)
        for _player in fetch_game.players:
            if _player.name == fetch_game.creator:  # TODO
                self.send(_player.peer, packets.server.cmd_fetch_game(player.sid))

    # TODO fix
    def onsavegamedata(self, player, packet):
        game = player.game

        for _player in game.players:
            if _player.sid == packet.psid:
                self.send(_player.peer, packets.server.savegame_data(packet.data, player.sid, game.mapname))

    def print_statistic(self, file):
        try:
            fd = open(file, "w")

            fd.write("Games.Total: %d\n" % (len(self.games)))
            games_playing = 0
            for game in self.games:
                if game.state is Game.State.Running:
                    games_playing += 1
            fd.write("Games.Playing: %d\n" % (games_playing))

            fd.write("Players.Total: %d\n" % (len(self.players)))
            players_inlobby = 0
            players_playing = 0
            players_oldprotocol = 0
            for player in self.players.values():
                if player.game is None:
                    continue
                if player.game.state is Game.State.Running:
                    players_playing += 1
                else:
                    players_inlobby += 1
                if player.protocol < PROTOCOLS[-1]:
                    players_oldprotocol += 1
            fd.write("Players.Lobby: %d\n" % (players_inlobby))
            fd.write("Players.Playing: %d\n" % (players_playing))
            fd.write("Players.OldProtocol: %d\n" % (players_oldprotocol))

            fd.close()
        except IOError as e:
            logging.error("[STATISTIC] Unable to open statistic file: %s" % (e))
        return
