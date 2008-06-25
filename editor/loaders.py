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

	cellgrid = fife.SquareGrid(True)
	cellgrid.thisown = 0
	cellgrid.setRotation(0)
	cellgrid.setXScale(1)
	cellgrid.setYScale(1)
	cellgrid.setXShift(0)
	cellgrid.setYShift(0)

	map = engine.getModel().createMap("map")

	layers = []
	for i in xrange(0,2):
		layers.append(map.createLayer(str(i), cellgrid))
	view = engine.getView()

	cam = view.addCamera("main", layers[len(layers) - 1], fife.Rect(0, 0, 1024, 768), fife.ExactModelCoordinate(0.0, 0.0, 0.0))
	cam.setCellImageDimensions(32, 16)
	cam.setRotation(45.0)
	cam.setTilt(-60)
	cam.setZoom(1)

	for (x, y, ground_id) in db("select x, y, ground_id from island.ground"):
		instance = layers[0].createInstance(engine.getModel().getObject(str(ground_id), 'ground'), fife.ModelCoordinate(int(x), int(y), 0), str(x) + ',' + str(y))
		fife.InstanceVisual.create(instance)
		instance.thisown = 0

	db("detach island")

def _save(file, engine, map):
	if not db("attach ? AS island", file).success:
		raise WrongFileType(file)

	print 'todo'

	db("detach island")

def pathsplit(p, rest=[]):
	(h,t) = os.path.split(p)
	if len(h) < 1: return [t]+rest
	if len(t) < 1: return [h]+rest
	return pathsplit(h,[t]+rest)

def commonpath(l1, l2, common=[]):
	if len(l1) < 1: return (common, l1, l2)
	if len(l2) < 1: return (common, l1, l2)
	if l1[0] != l2[0]: return (common, l1, l2)
	return commonpath(l1[1:], l2[1:], common+[l1[0]])

def relpath(p1, p2):
	(common,l1,l2) = commonpath(pathsplit(p1), pathsplit(p2))
	p = []
	if len(l1) > 0:
		p = [ '../' * len(l1) ]
	p = p + l2
	return os.path.join( *p )

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
			img = engine.getImagePool().addResourceFromFile(relpath(os.getcwd(), os.path.abspath(os.path.dirname(__file__) + '/../' + str(file))))
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
