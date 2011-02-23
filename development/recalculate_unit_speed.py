#!/usr/bin/env python
# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.orgk
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
import sys
import os.path
import sqlite3

if __name__ == "__main__":

	usage = '''Parameter:
	-u num: recalculate velocity for unit num
	-g num: recalculate velocity for ground num

If you e.g. change the velocity modifier for ground 2, run this script with '-g 2'.
		'''


	dbfile = 'content/game.sqlite'

	if not os.path.exists(dbfile):
		print 'Please execute from unknown-horizons root directory.'
		sys.exit(1)

	# copied from dbreader.py:
	con = sqlite3.connect(dbfile)
	con.isolation_level = None
	con.text_factory = str

	cur = con.cursor()

	def db(cmd, *args):
		cur.execute(cmd, args)
		return cur.fetchall()

	def check_rounding_error(val, unit, groundid, diagonal):
		if abs(val - round(val)) >= 0.4:
			if diagonal:
				print 'warning: big rounding error for DIAGONAL move'
			else:
				print 'warning: big rounding error'

			print 'unit:',unit,' ground:',groundid
			print 'raw value %.4f  rounded: %d'%(val, int(val))
			print

	def update(unit, groundid, base_vel, vel_mod):
		if len(db("SELECT rowid FROM unit_velocity WHERE unit = ? AND ground = ?;", unit, groundid)) > 0:
			db("DELETE FROM unit_velocity WHERE unit = ? AND ground = ?", unit, groundid)

		straight = base_vel * vel_mod
		check_rounding_error(straight, unit, groundid, False)

		diagonal = straight * 2**0.5
		check_rounding_error(diagonal, unit, groundid, True)

		db("INSERT INTO unit_velocity(unit, ground, time_move_straight, time_move_diagonal) VALUES(?, ?, ?, ?)", unit, groundid, int(round(straight)), int(round(diagonal)))


	argv = sys.argv

	if len(argv) != 3:
		print usage
		sys.exit(0)

	print '-'*8,'USE AT OWN RISK','-'*8
	print 'NOTE: previous values will be overwritten, manually entered changes will be lost'
	print 'Are you sure you want to run this script with these params:',sys.argv[1:],'? (y/n)'
	if raw_input() != 'y':
		print 'Aborting'
		sys.exit(0)


	print 'If your specified number does not exist in the db, nothing will happen'


	if sys.argv[1] == '-u':
		unit = int(sys.argv[2])
		print 'Recalculating for unit', unit
		for base_vel, in db("SELECT base_velocity FROM unit WHERE rowid = ?;", unit):
			for groundid, vel_mod in db("SELECT rowid, velocity_modifier FROM ground"):
				update(unit, groundid, base_vel, vel_mod)
		print 'Done. If no warnings occurred, then you chose good values'

	elif sys.argv[1] == '-g':
		groundid = int(sys.argv[2])
		print 'Recalculating for ground', groundid
		for vel_mod, in db("SELECT velocity_modifier FROM ground WHERE rowid = ?", groundid):
			for unit, base_vel in db("SELECT rowid, base_velocity FROM unit"):
				update(unit, groundid, base_vel, vel_mod)
		print 'Done. If no warnings occurred, then you chose good values'

	else:
		print usage
