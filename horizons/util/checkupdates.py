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

import json
import platform
import threading
import urllib.error
import urllib.request
import webbrowser

from fife.extensions.pychan.widgets import Button

import horizons.main
from horizons.constants import NETWORK, VERSION
from horizons.extscheduler import ExtScheduler
from horizons.gui.windows import Popup
from horizons.i18n import gettext as T
from horizons.util.python.callback import Callback


TIMEOUT = 5.0 # we should be done before the user can start a game


def is_version_newer(original, candidate):
	"""
	Returns whether the version identifier `candidate` is a newer version than `original`.
	"""
	def parse(value):
		return tuple(map(int, value.split('.')))

	try:
		return parse(candidate) > parse(original)
	except (AttributeError, ValueError):
		return False


def check_for_updates():
	"""
	Check if there's a new version, returns the data from the server, otherwise None.
	"""
	# no updates for git version
	if VERSION.IS_DEV_VERSION:
		return

	# only updates for operating systems missing a package management
	if platform.system() not in ('Windows', 'Darwin'):
		return

	try:
		with urllib.request.urlopen(NETWORK.UPDATE_FILE_URL, timeout=TIMEOUT) as f:
			data = json.loads(f.read())
			if is_version_newer(VERSION.RELEASE_VERSION, data['version']):
				return data
	except (urllib.error.URLError, ValueError, KeyError):
		pass


class VersionHint(Popup):
	def __init__(self, windows, data):
		self.data = data

		title = T("New version of Unknown Horizons")
		text = T("There is a more recent release of Unknown Horizons ({new_version}) "
				 "than the one you are currently using ({old_version}).").format(
				new_version=data['version'],
				old_version=VERSION.RELEASE_VERSION)

		super().__init__(windows, title, text)

	def prepare(self, **kwargs):
		super().prepare(**kwargs)

		dl_btn = Button(name="dl", text=T("Click to download"))
		dl_btn.position = (48, 138) # i've tried, this button cannot be placed in a sane way
		def do_dl():
			webbrowser.open(self.data['download_url'])
			dl_btn.text = T("A page has been opened in your browser.")
			self._gui.adaptLayout()
		dl_btn.capture(do_dl)

		self._gui.addChild(dl_btn)


def setup_async_update_check():
	"""
	Requests information about the newest release from our website inside a thread, so the
	user interface isn't blocked.
	"""

	# Store result from thread in a variable of the main thread. If we were to access FIFE
	# from another thread, it tends to fail.
	result = None
	def wrapper():
		nonlocal result
		result = check_for_updates()

	thread = threading.Thread(target=wrapper)
	thread.start()

	def wait_for_task():
		"""
		Continuously check whether the thread is done.
		"""
		if thread.is_alive():
			ExtScheduler().add_new_object(wait_for_task, None)
		else:
			if result:
				gui = horizons.main._modules.gui
				window = VersionHint(gui.windows, result)
				gui.windows.open(window)
			else:
				# couldn't retrieve file or nothing relevant in there
				pass

	wait_for_task()
