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

import pychan

class IngameGui():
    """Class handling all the ingame gui events."""
    def __init__(self):
        self.status = pychan.loadXML('content/gui/status.xml')
        self.status.show()
        self.minimap = pychan.loadXML('content/gui/minimap.xml')
        self.minimap.show()

    def status_set(self, label, value):
        """Sets a value on the status bar.
        @var label: str containing the name of the label to be set.
        @var value: value the Label is to be set to.
        """
        foundlabel = self.status.findChild(name=label)
        foundlabel._setText(value)
        foundlabel.resizeToContent()
        self.status.resizeToContent()
