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

import os
import subprocess
import sys
import time

import horizons
import horizons.globals
from horizons.constants import GFX, PATHS


def generate_atlases():
	"""
	Generate atlases in dev mode. Shows a TK window during the process.
	"""
	try:
		import tkinter
		from PIL import Image, ImageTk
	except ImportError:
		# tkinter or PIL may be missing, abort
		return

	horizons_path = os.path.dirname(horizons.__file__)
	args = [sys.executable, os.path.join(horizons_path, 'engine', 'generate_atlases.py'),
		str(horizons.globals.fife.get_uh_setting('MaxAtlasSize'))]
	process = subprocess.Popen(args, stdout=None, stderr=subprocess.STDOUT)

	try:
		window = tkinter.Tk()
		# iconify window instead of closing
		window.protocol("WM_DELETE_WINDOW", window.iconify)
		window.wm_withdraw()
		window.attributes("-topmost", 1)
		window.title("Unknown Horizons")
		window.maxsize(300, 150)

		logo = Image.open(PATHS.UH_LOGO_FILE)
		res_logo = logo.resize((116, 99), Image.ANTIALIAS)
		res_logo_image = ImageTk.PhotoImage(res_logo)
		logo_label = tkinter.Label(window, image=res_logo_image)
		logo_label.pack(side="left")
		label = tkinter.Label(window, padx=10, text="Generating atlases!")
		label.pack(side="right")

		window.deiconify()
		window.attributes("-topmost", 0)
		while process.poll() is None:
			if not window.state() == "iconic":
				window.update()
			time.sleep(0.1)
		window.destroy()

		if process.returncode != 0:
			print('Atlas generation failed. Continuing without atlas support.')
			print('This just means that the game will run a bit slower.')
			print('It will still run fine unless there are other problems.')
			print()
		else:
			GFX.USE_ATLASES = True
			PATHS.DB_FILES = PATHS.DB_FILES + (PATHS.ATLAS_DB_PATH, )
	except tkinter.TclError:
		# catch #2298
		pass
