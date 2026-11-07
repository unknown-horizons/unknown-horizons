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

import pytest

from horizons.messaging.simplemessagebus import SimpleMessageBus


def test_simple_bus_broadcast():
    bus = SimpleMessageBus(('event1', 'event2'))
    callback = pytest.importorskip("unittest.mock").Mock()

    bus.subscribe('event1', callback)
    bus.broadcast('event1', "hello", key="world")

    callback.assert_called_once_with("hello", key="world")

def test_simple_bus_unsupported_type():
    bus = SimpleMessageBus(('event1',))

    with pytest.raises(TypeError, match="Unsupported type"):
        bus.subscribe('unknown', lambda: None)

def test_simple_bus_duplicate_subscription():
    bus = SimpleMessageBus(('event1',))
    callback = lambda: None

    bus.subscribe('event1', callback)
    with pytest.raises(Exception, match="already subscribed"):
        bus.subscribe('event1', callback)

def test_simple_bus_discard_and_unsubscribe():
    bus = SimpleMessageBus(('event1',))
    callback = lambda: None

    bus.subscribe('event1', callback)

    # Test unsubscribe
    bus.unsubscribe('event1', callback)
    assert len(bus._callbacks['event1']) == 0

    # Test discard (should not raise error even if not present)
    bus.discard('event1', callback)
