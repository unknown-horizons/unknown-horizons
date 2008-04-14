# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify 
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

import threading

class TimerManager():
    """"Class providing a thread for timed callbacks.
    To start a timed callback, either create a CallbackObject with the apropriat values and call add_object(),
    or call add_new_object() to make the TimingThread Class create a CallbackObject for you.
    Currentl this class is might support up to 1000+ timed callbacks. Performace will suffer with increasing
    number of timed callbacks.
    """
    def __init__(self):
        self.timerlist = []

    def run(self, object):
        """Threads main loop
        @var object: callbackObject instance, which's callback is to be used.
        @var oldtimer: Timer object, that is to be destructed."""
        self.timerlist.remove(object.timer)
        object.callback()
        if object.loops is not -1:
            object.loops -= 1
        if object.loops is not 0:
            timer = threading.Timer(object.runin, self.run, (object,))
            self.timerlist.append(timer)
            object.timer = timer
            timer.start()

    def stop_all(self):
        """Stops all running timers."""
        for timer in self.timerlist:
            timer.cancel()
            self.timerlist.remove(timer)

    def add_object(self, object):
        """Adds a new CallbackObject instance to the callbacks list
        @var object: CallbackObject type object, containing all neccessary  information
        """
        timer = threading.Timer(object.runin, self.run, (object,))
        object.timer = timer
        self.timerlist.append(timer)
        timer.start()

    def add_new_object(self, runin, callback, loops):
        """Creates a new CallbackObject instance and calls the self.add_object() function.
        @var runing: int time in seconds regulating after how long the callback is called.
        @var callback: function callback, which is called after time seconds.
        @var loops: How often the callback is called. -1 = infinit  times."""
        object = CallbackObject(runin, callback, loops)
        self.add_object(object)


class CallbackObject():
    """Class used by the TimerManager Class to organize callbacks."""
    def __init__(self, runin, callback, loops):
        """Creates the CallbackObject instance.
        @var runin: int time in seconds, regulating after how long the callback is called.
        @var callback: function callback, which is called after time seconds.
        @var loops: How often the callback is called. -1 = infinit times.
        """
        self.runin = runin
        self.callback = callback
        self.loops = loops
        self.timer = None
