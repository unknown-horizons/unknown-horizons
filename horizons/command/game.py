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

from horizons.command import Command
from horizons.savegamemanager import SavegameManager

class SaveCommand(Command):
	"""Used to init a save, which will happen at all network machines.
	Only reasonable in multiplayer games."""
	def __init__(self, name):
		self.name = name

	def __call__(self, issuer):
		session = issuer.session
		try:
			path = SavegameManager.create_multiplayersave_filename(self.name)
		except RuntimeError, e:
			headline = _("Invalid filename")
			msg = _("Received an invalid filename for a save command.")
			session.gui.show_error_popup(headline, msg, unicode(e))
			return

		self.log.debug("SaveCommand: save to %s", path)

		success = session._do_save( path )
		if success:
			session.ingame_gui.message_widget.add(None, None, 'SAVED_GAME') # TODO: distinguish auto/quick/normal
		else:
			session.gui.show_popup(_('Error'), _('Failed to save.'))

Command.allow_network(SaveCommand)
