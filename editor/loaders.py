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

def load(file, engine):
	global _inited
	if not _inited:
		init(engine)
		_inited = True

	if not db("attach ? AS island", file).success:
		raise WrongFileType(file)

	print 'todo'

	db("detach island")

def save(file, engine, map):
	print 'save(file = ', file, ', engine, map = ', map, ')'

def init(engine):
	global db
	db = DbReader(':memory:')
	db("attach ? AS data", os.path.abspath(os.path.basename(__file__) + '/../content/openanno.sqlite'))

def loadMapFile(path, engine, content = ''):
	load(path, engine)

def saveMapFile(path, engine, map, importList=[]):
	save(path, engine, map)

def loadImportFile(path, engine):
	pass

def loadImportDir(path, engine):
	pass

def loadImportDirRec(path, engine):
	pass
