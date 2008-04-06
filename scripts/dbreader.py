# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

import sqlite3

class DbReader:
    """Class that handles connections to sqlite databases"""
    
    def __init__(self, file):
        """Init function, opens the connection to a database and creates a cursor for that database
        @var file: str containing the database file.
        """
        self.connection = sqlite3.connect(file)
        self.connection.isolation_level = None
        self.cur = self.connection.cursor()

    def query(self, command, vals = ()):
        """Executes a sql command. 
        @var command: str containing the raw sql command, with ? as placeholders for values (eg. SELELCT ? FROM ?).
        @var vals: tuple containing the values to add into the command.
        """ 
        ret = SqlResult()
        if not sqlite3.complete_statement(command):
            if sqlite3.complete_statement(command + ';'):
                command = command + ';'
            else:
                raise "Error, no complete sql statement provided by \"",command,"\"."
        try:
            if type(vals) is str().__class__:
                vals = (vals,)
            elif type(vals) is tuple().__class__:
                vals = (vals+())
            self.cur.execute(command, vals)
            ret.rows = self.cur.fetchall()
            ret.affected = self.cur.rowcount
            if ret.affected is -1:
                ret.affected = None
        except sqlite3.Error, e:
            print "An error occurred:", e.args[0]
            ret.success = False
            ret.error = e.args[0]
        return ret

    def execute_script(self, script):
        """Executes a multiline script.
        @var script: multiline str containing an sql script."""
        return self.cur.executescript(script)

class SqlResult:
    """Represents a SQL result"""
    def __init__(self):
        self.success = True
        self.rows = None
        self.error = None
        self.affected = None
