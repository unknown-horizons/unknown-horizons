# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import webbrowser
import urllib
import urllib2

from fife.extensions import pychan

from horizons.constants import NETWORK, VERSION
from horizons.gui.widgets import OkButton

class UpdateInfo(object):
	INVALID, READY, UNINITIALISED = range(3)
	def __init__(self):
		self.status = UpdateInfo.UNINITIALISED
		self.version = None
		self.link = None

TIMEOUT = 5.0 # we should be done before the user can start a game
def check_for_updates(info):
	"""Check if there's a new version.
	@return update file contents or None"""
	# make sure to always set info.status, but only when we're done
	if VERSION.IS_DEV_VERSION: # no updates for git version
		info.status = UpdateInfo.INVALID
		return

	# retrieve current version w.r.t. the local version.
	# this way, possible configurations of different most recent versions should be handleable in the future.
	data = urllib.urlencode( {"my_version" : VERSION.RELEASE_VERSION} )
	url = NETWORK.UPDATE_FILE_URL
	try:
		u = urllib2.urlopen( url + "?" + data, timeout=TIMEOUT )
	except urllib2.URLError as e:
		print 'Failed to check for updates: ', e
		info.status = UpdateInfo.INVALID
		return

	version = u.readline()
	link = u.readline()
	u.close()

	version = version[:-1] # remove newlines
	link = link[:-1] # remove newlines

	if version != VERSION.RELEASE_VERSION:
		# there is a new version
		info.version = version
		info.link = link
		info.status = UpdateInfo.READY
	else:
		info.status = UpdateInfo.INVALID

def show_new_version_hint(gui, info):
	"""
	@param gui: main gui (Gui)
	@param info: UpdateInfo instance
	"""
	title = _(u"New version of Unknown Horizons")
	#xgettext:python-format
	text = _(u"There is a more recent release of Unknown Horizons ({new_version}) than the one you are currently using ({old_version}).").format(
	        new_version=info.version,
	        old_version=VERSION.RELEASE_VERSION)

	dl_btn = pychan.widgets.Button(name="dl", text=_("Click to download"))
	dl_btn.position = (48, 138) # i've tried, this button cannot be placed in a sane way
	def do_dl():
		webbrowser.open(info.link)
		dl_btn.text = _("A page has been opened in your browser.")
		popup.adaptLayout()
	dl_btn.capture(do_dl)

	popup = gui.build_popup(title, text)
	popup.addChild( dl_btn )

	gui.show_dialog(popup, {OkButton.DEFAULT_NAME : True}, modal=True)
