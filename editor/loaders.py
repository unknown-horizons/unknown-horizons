# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from dbreader import DbReader
from fife import fife
from serializers import WrongFileType
import os.path

fileExtensions = ('sqlite',)
_inited = False

from plugins.mapwizard import MapWizard
import plugins.plugin
class myMapWizard(plugins.plugin.Plugin):
	def __init__(self, engine):
		self.engine = engine
		self.menu_items = { 'New Map' : self.new_map }
		self.newMap = None
		self.new_map()

	def new_map(self):
		self.map = _empty(self.engine)
		self.newMap = self.map
plugins.mapwizard.MapWizard = myMapWizard

def _empty(engine):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True
	cellgrid = fife.SquareGrid(True)
	cellgrid.thisown = 0
	cellgrid.setRotation(0)
	cellgrid.setXScale(1)
	cellgrid.setYScale(1)
	cellgrid.setXShift(0)
	cellgrid.setYShift(0)

	engine.getModel().deleteMaps()
	map = engine.getModel().createMap("island")

	layer = map.createLayer('ground', cellgrid)
	layer.setPathingStrategy(fife.CELL_EDGES_AND_DIAGONALS)
	view = engine.getView()

	view.clearCameras()
	cam = view.addCamera("main", layer, fife.Rect(0, 0, 1024, 768))
	cam.setCellImageDimensions(64, 32)
	cam.setRotation(315.0)
	cam.setTilt(-60)
	cam.setZoom(1)

	return map

def _load(file, engine):
	if not db("attach ? AS island", file).success:
		raise WrongFileType(file)

	map = _empty(engine)
	map.setResourceFile(file)
	layer = map.getLayer('ground')

	nr = 0
	already = []
	for (x, y, ground_id) in db("select x, y, ground_id from island.ground"):
		if (int(x), int(y)) not in already:
			instance = layer.createInstance(engine.getModel().getObject(str(ground_id), 'ground'), fife.ModelCoordinate(int(x), int(y), 0), str(nr))
			location = fife.Location(layer)
			location.setLayerCoordinates(fife.ModelCoordinate(int(x + 1), int(y), 0))
			instance.setFacingLocation(location)
			fife.InstanceVisual.create(instance)
			instance.thisown = 0
			nr+=1
			already.append((int(x), int(y)))
	#except:
	#	raise WrongFileType(file)

	db("detach island")

	map.importDirs = []
	return map

def _save(file, engine, map):
	if not db("attach ? AS island", file).success:
		raise WrongFileType(file)

	try:
		if not db('create table island.ground (x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL)').success:
			raise int #just throw anything, int was the first i thought of...
	except:
		db('delete from island.ground')

	try:
		if not db('CREATE TABLE island.island_properties (name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)').success:
			raise int
	except:
		db('delete from island.island_properties')

	layer = map.getLayer('ground')

	instances = layer.getInstances()

	already = []
	for instance in instances:
		coord = instance.getLocation().getLayerCoordinates()
		x, y = int(coord.x), int(coord.y)
		if (int(x), int(y)) not in already:
			ground_id = int(instance.getObject().getId().split(':')[0])
			rotation = instance.getRotation()
			if rotation != 0:
				ground_id = db('select rowid from data.ground where animation_45 = (select animation_%d from data.ground where rowid = ? limit 1) limit 1' % ((rotation + 45) % 360,), ground_id)[0][0]
			db('insert into island.ground (x, y, ground_id) values (?, ?, ?)',x, y, ground_id)
			already.append((int(x), int(y)))

	db("detach island")

def pathsplit(p, rest=[]):
	(h, t) = os.path.split(p)
	if len(h) < 1: return [t]+rest
	if len(t) < 1: return [h]+rest
	return pathsplit(h,[t]+rest)

def commonpath(l1, l2, common=[]):
	if len(l1) < 1: return (common, l1, l2)
	if len(l2) < 1: return (common, l1, l2)
	if l1[0] != l2[0]: return (common, l1, l2)
	return commonpath(l1[1:], l2[1:], common+[l1[0]])

def relpath(p1, p2):
	(common, l1, l2) = commonpath(pathsplit(p1), pathsplit(p2))
	p = []
	if len(l1) > 0:
		p = [ '../' * len(l1) ]
	p = p + l2
	return os.path.join( *p )

def _init(engine):
	global db
	db = DbReader(':memory:')
	db("attach ? AS data", os.path.abspath(os.path.dirname(__file__) + '/../content/game.sqlite'))

	for (ground_id, animation_45, animation_135, animation_225, animation_315) in db("SELECT rowid, (select file from data.animation where animation_id = animation_45 limit 1), (select file from data.animation where animation_id = animation_135 limit 1), (select file from data.animation where animation_id = animation_225 limit 1), (select file from data.animation where animation_id = animation_315 limit 1) FROM data.ground"):
		print 'Loading ground #%i ...' % (ground_id)
		name = os.path.basename(animation_45)
		object = engine.getModel().createObject(str(ground_id) + ":" +str(name), 'ground')
		object.thisown = 0
		fife.ObjectVisual.create(object)
		visual = object.get2dGfxVisual()

		for rotation, file in [(45, animation_45), (135, animation_135), (225, animation_225), (315, animation_315)]:
			img = engine.getImagePool().addResourceFromFile(relpath(os.getcwd(), os.path.abspath(os.path.dirname(__file__) + '/../' + file)))
			visual.addStaticImage(int(rotation), img)
			img = engine.getImagePool().getImage(img)
			img.setXShift(0)
			img.setYShift(0)

def loadMapFile(path, engine, content = ''):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True
	return _load(path, engine)

def saveMapFile(path, engine, map, importList=[]):
	global _inited
	if not _inited:
		_init(engine)
		_inited = True
	return _save(path, engine, map)

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
