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

    def execute_command(self, command, vals):
        """Executes a sql command. 
        @var command: str containing the raw sql command, with ? as placeholders for values (eg. SELELCT ? FROM ?).
        @var vals: tuple containing the values to add into the command.
        """ 
        if sq3lite.complete_statement(command):
            try:
                self.cur.execute(command, vals)
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]
        else:
            print "Error, no complete sql statement provided by \"",command,"\"."
        if command.startswith("SELECT"): 
            return self.cur.fetchall()
        else:
            return self.cur

    def execute_select(self, item, fr, search, value):
        """Executes a SELECT statement
        executes "SELECT item FROM fr WHERE search='value'"
        @var item: str, see above.
        @var fr: str, see above.
        @var search: str, see above.
        @var value: str, see above.
        """
        return self.execute_command("SELECT ? FROM ? WHERE ?='?';", (item, fr, search, value))

    def execute_script(self, script):
        """Executes a multiline script.
        @var script: multiline str containing an sql script."""
        return self.cur.executescript(script)


