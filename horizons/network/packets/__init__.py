# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

import cPickle

from horizons.network import find_enet_module
enet = find_enet_module()


__version__ = '0.1'
__all__ = [
  'packet',
  'packetlist'
]

PICKLE_PROTOCOL = 2

packetlist = []

class packet:
  def serialize(self):
    return cPickle.dumps(self, PICKLE_PROTOCOL)

  def send(self, peer, channelid = 0):
    packet = enet.Packet(self.serialize(), enet.PACKET_FLAG_RELIABLE)
    peer.send(channelid, packet)

#-------------------------------------------------------------------------------

class cmd_ok(packet):
  """simple ok message"""

packetlist.append(cmd_ok)

#-------------------------------------------------------------------------------

class cmd_error(packet):
  def __init__(self, errorstr):
    self.errorstr = errorstr

packetlist.append(cmd_error)

#-------------------------------------------------------------------------------

class cmd_fatalerror(packet):
  def __init__(self, errorstr):
    self.errorstr = errorstr

packetlist.append(cmd_fatalerror)

#-------------------------------------------------------------------------------

def unserialize(data):
  try:
    packet = cPickle.loads(data)
  except Exception:
    return None

  for packetclass in packetlist:
    if (isinstance(packet, packetclass)):
      return packet
  return None

#-------------------------------------------------------------------------------

import horizons.network.packets.server
import horizons.network.packets.client
import horizons.network.packets.p2p

