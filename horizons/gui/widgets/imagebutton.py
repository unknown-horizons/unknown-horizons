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

from fife.extensions.pychan.widgets import ImageButton


class OkButton(ImageButton):
	"""The OkButton is a shortcut for an ImageButton with our OK / apply icon.
	Its default attributes are:
	name="okButton"
	up_image="content/gui/images/buttons/ok.png"
	hover_image="content/gui/images/buttons/ok_h.png"
	down_image="content/gui/images/buttons/ok.png"
	"""
	def __init__(self, name='okButton', **kwargs):
		super(OkButton, self).__init__(
			name=name,
			is_focusable = False,
			up_image="content/gui/images/buttons/ok.png",
			hover_image="content/gui/images/buttons/ok_h.png",
			down_image="content/gui/images/buttons/ok.png", **kwargs)
	def setInactive(self,state=True):
		if(state):
			self.up_image = "content/gui/images/buttons/ok_bw.png"
			self.down_image = "content/gui/images/buttons/ok_bw.png"
			self.hover_image = "content/gui/images/buttons/ok_bw.png"
		else:
			self.up_image = "content/gui/images/buttons/ok.png"
			self.down_image = "content/gui/images/buttons/ok_h.png"
			self.hover_image = "content/gui/images/buttons/ok.png"			

class CancelButton(ImageButton):
	"""The CancelButton is a shortcut for an ImageButton with our cancel / close
	icon. Its default attributes are:
	name="cancelButton"
	up_image="content/gui/images/buttons/close.png"
	hover_image="content/gui/images/buttons/close_h.png"
	down_image="content/gui/images/buttons/close.png"
	"""
	def __init__(self, name='cancelButton', **kwargs):
		super(CancelButton, self).__init__(
			name=name,
			is_focusable = False,
			up_image="content/gui/images/buttons/close.png",
			hover_image="content/gui/images/buttons/close_h.png",
			down_image="content/gui/images/buttons/close.png", **kwargs)
	def setInactive(self,state=True):
		if(state):
			self.up_image = "content/gui/images/buttons/close_bw.png"
			self.down_image = "content/gui/images/buttons/close_bw.png"
			self.hover_image = "content/gui/images/buttons/close_bw.png"
		else:
			self.up_image = "content/gui/images/buttons/close.png"
			self.down_image = "content/gui/images/buttons/close_h.png"
			self.hover_image = "content/gui/images/buttons/close.png"

class DeleteButton(ImageButton):
	"""The DeleteButton is a shortcut for an ImageButton with our delete / tear
	icon. Its default attributes are:
	name="deleteButton"
	up_image="content/gui/images/buttons/delete.png"
	hover_image="content/gui/images/buttons/delete_h.png"
	down_image="content/gui/images/buttons/delete.png"
	"""
	def __init__(self, name='deleteButton',  **kwargs):
		super(DeleteButton, self).__init__(
			name=name,
			is_focusable = False,
			up_image="content/gui/images/buttons/delete.png",
			hover_image="content/gui/images/buttons/delete_h.png",
			down_image="content/gui/images/buttons/delete.png", **kwargs)
	def setInactive(self,state=True):
		if(state):
			self.up_image = "content/gui/images/buttons/delete_bw.png"
			self.down_image = "content/gui/images/buttons/delete_bw.png"
			self.hover_image = "content/gui/images/buttons/delete_bw.png"
		else:
			self.up_image = "content/gui/images/buttons/delete.png"
			self.down_image = "content/gui/images/buttons/delete_h.png"
			self.hover_image = "content/gui/images/buttons/delete.png"
