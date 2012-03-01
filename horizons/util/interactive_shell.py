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

from IPython.zmq.ipkernel import Kernel
from IPython.zmq.kernelapp import KernelApp

from horizons.gui.mousetools.selectiontool import SelectionTool


def pick_object(self, args):
	"""Intercepts selection of buildings/units and puts a reference to the object
	into the namespace of the IPython shell.

	In the shell, execute the following:

		%uhpick

	Now select a building or unit, and the object is accessible as variable `selection`.
	"""
	original = SelectionTool.apply_select
	shell = self

	def deco(func):
		def wrapped(self, *args, **kwargs):
			if self.session.selected_instances:
				shell.push({'selection': list(self.session.selected_instances)[0]})
				SelectionTool.apply_select = original
			return func(self, *args, **kwargs)
		return wrapped

	SelectionTool.apply_select = deco(SelectionTool.apply_select)


class UHKernel(Kernel):
	"""Custom kernel to inject a callback into the fifengine."""
	def start(self):
		self.shell.define_magic('uhpick', pick_object)
		self.fife_engine.pump.append(self.do_one_iteration)


class UHKernelApp(KernelApp):
	kernel_class = 'horizons.util.interactive_shell.UHKernel'


def start(engine):
	"""
	Starts an IPython kernel, that's basically an interactive shell running in this
	process. However the input is handled by frontends running in other processes.

	Once this kernel is running, you can connect to it with:

		ipython console --existing

	Read the IPython docs for more information (`ipython.org/ipython-doc`_).
	"""
	app = UHKernelApp.instance()
	# pass empty argv, otherwise IPython chokes on existing commandline parameters
	app.initialize(argv=[])
	app.kernel.fife_engine = engine
	app.start()
