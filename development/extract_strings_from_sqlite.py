#!/usr/bin/python
# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

class SettlerLevel(Base):
    __tablename__ = 'settler_level'

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

def print_msgid(msgid):
    print 'msgid "%s"\nmsgstr ""\n' % msgid

for building in session.query(Building):
    print_msgid(building.name)

for unit in session.query(Unit):
     print_msgid(unit.name)

for settler_level in session.query(SettlerLevel):
     print_msgid(settler_level.name)

for color in session.query(Colors):
     print_msgid(color.name)

for message in session.query(Message):
     print_msgid(message.text)

for resource in session.query(Resource):
     print_msgid(resource.name)
