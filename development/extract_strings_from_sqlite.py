#!/usr/bin/env python3

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

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** Refer to  development/create_pot.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################
#
# THIS SCRIPT IS A HELPER SCRIPT. DO NOT INVOKE MANUALLY!
#
###############################################################################

from __future__ import print_function
import os
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlite3
import sys
import tempfile
from collections import defaultdict

sys.path.append(".")
sys.path.append("./horizons")

from horizons.constants import PATHS


# sqlalchemy doesn't support importing sql files,
# therefore we work around this by using sqlite3

filename = tempfile.mkstemp(text=True)[1]
conn = sqlite3.connect(filename)

for db_file in PATHS.DB_FILES:
	conn.executescript(open(db_file, "r").read())

conn.commit()

engine = sqlalchemy.create_engine('sqlite:///' + filename) # must be 4 slashes total, sqlalchemy breaks the unixoid conventions here

Session = sqlalchemy.orm.sessionmaker(bind=engine)
db_session = Session()

Base = sqlalchemy.ext.declarative.declarative_base()


#
# Classes
#
class Message(Base):
	__tablename__ = 'message_text'

	text = sqlalchemy.Column(sqlalchemy.String, primary_key=True)


class Resource(Base):
	__tablename__ = 'resource'

	name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)


class Tier(Base):
	__tablename__ = 'tier'

	name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

#
# print it
#


class MSGID_collect:
	msgids = defaultdict(list)

	def __init__(self):
		pass

	def add_to_collection(self, msgid, place):
		self.msgids[msgid].append(place)

	def __str__(self):
		s = []
		for text, locations in self.msgids.items():
			comment = '#. This is a database entry: {}\n'.format(','.join(locations))
			s += [comment + build_msgid(text)]
		return '\n'.join(s).strip()


def build_msgid(msgid):
	return 'msgid "{}"\nmsgstr ""\n'.format(msgid.replace('"', '\\"'))


def collect_all():
	collector = MSGID_collect()

	for message in db_session.query(Message):
		collector.add_to_collection(message.text, 'a messagewidget message (left part of the screen)')

	for resource in db_session.query(Resource):
		collector.add_to_collection(resource.name, 'the name of a resource')

	for tier in db_session.query(Tier):
		collector.add_to_collection(tier.name, 'the name of an inhabitant tier (level)')

	return collector


print(collect_all())
os.unlink(filename)
