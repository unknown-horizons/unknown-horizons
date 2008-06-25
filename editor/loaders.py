# ###################################################
# Copyright (C) 2008 The OpenAnno Team
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

from dbreader import DbReader
import fife
from serializers import WrongFileType
import os.path

fileExtensions = ('sqlite',)
_inited = False
def _load(file, engine):
	if not db("attach ? AS island", file).success:
		raise WrongFileType(file)

	print 'todo'

	db("detach island")

def _save(file, engine, map):
	if not db("attach ? AS island", file).success:
		raise WrongFileType(file)

	print 'todo'

	db("detach island")

def _init(engine):
	global db
	db = DbReader(':memory:')
	db("attach ? AS data", os.path.abspath(os.path.dirname(__file__) + '/../content/openanno.sqlite'))

	for (ground_id,) in db("SELECT rowid FROM data.ground"):
		print 'Loading ground #' + str(ground_id) + '...'
		object = engine.getModel().createObject(str(ground_id), 'ground')
		object.thisown = 0
		fife.ObjectVisual.create(object)
		visual = object.get2dGfxVisual()

		for rotation, file in db("SELECT rotation, (select file from data.animation where data.animation.animation_id = data.action.animation order by frame_end limit 1) FROM data.action where ground=?", ground_id):
			img = engine.getImagePool().addResourceFromFile(os.path.abspath(os.path.dirname(__file__) + '/../' + str(file)))
			visual.addStaticImage(int(rotation), img)
			img = engine.getImagePool().getImage(img)
			img.setXShift(0)
			img.setYShift(0)

def loadMapFile(path, engine, content = ''):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True
	_load(path, engine)

def saveMapFile(path, engine, map, importList=[]):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True
	_save(path, engine, map)

def loadImportFile(path, engine):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True

def loadImportDir(path, engine):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True

def loadImportDirRec(path, engine):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True
