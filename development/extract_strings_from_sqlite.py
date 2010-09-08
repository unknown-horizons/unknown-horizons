#!/usr/bin/env python
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

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

engine = sqlalchemy.create_engine('sqlite:///content/game.sqlite')
Session = sqlalchemy.orm.sessionmaker(bind=engine)
session = Session()

Base = sqlalchemy.ext.declarative.declarative_base()

#
# Classes
#

class Building(Base):
	__tablename__ = 'building'

	name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

class Unit(Base):
	__tablename__ = 'unit'

	name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

class Colors(Base):
	__tablename__ = 'colors'

	name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

class Message(Base):
	__tablename__ = 'message'

	text = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

class Resource(Base):
	__tablename__ = 'resource'

	name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

#
# print it
#

class MSGID_collect:
	msgids = dict()

	def __init__(self):
		pass

	def add_to_collection(self, msgid, place):
		if self.msgids.has_key(msgid):
			self.msgids[msgid].append(place)
		else:
			self.msgids[msgid] = [place]

	def __str__(self):
		s = []
		for pair in self.msgids.items():
			s += ['#: sqlite/%s\nmsgid "%s"\nmsgstr ""\n' % (' '.join(pair[1]), pair[0])]
		return '\n'.join(s).strip()

def collect_msgid(msgid, place):
	pass

def print_msgid(msgid):
	print 'msgid "%s"\nmsgstr ""\n' % msgid

def collect_all():
	collector = MSGID_collect()

	for building in session.query(Building):
		collector.add_to_collection(building.name, 'Building')

	for unit in session.query(Unit):
		collector.add_to_collection(unit.name, 'Unit')

	#for settler_level in session.query(SettlerLevel):
	#    print_msgid(settler_level.name)

	for color in session.query(Colors):
		collector.add_to_collection(color.name, 'Colors')

	for message in session.query(Message):
		collector.add_to_collection(message.text, 'Messages')

	for resource in session.query(Resource):
		collector.add_to_collection(resource.name, 'Resources')

	return collector

if __name__ == '__main__':
	print collect_all()
