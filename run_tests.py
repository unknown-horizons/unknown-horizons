#!/usr/bin/env python

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


import os
import sys
import openanno
import unittest

if __name__ == '__main__':
	# the usual setup:
	openanno.findFIFE()
	sys.path.append('game/ext')
	import game.main

	loader = unittest.TestLoader()
	result = unittest.TestResult()
	suite = unittest.TestSuite()

	from tests import *


	# add tests here:
	suite.addTest(loader.loadTestsFromModule(pathfinding))



	suite.run(result)


	print "\nRESULTS:\n"

	print result.testsRun, 'tests were run'
	print 'All successful:', result.wasSuccessful()

	if not result.wasSuccessful():

		print

		print len(result.failures),'Failures:'
		for (case, error) in result.failures:
			print 'Case:', case
			print error
			print

		print

		print len(result.errors),'Errors:'
		for (case, error) in result.errors:
			print 'Case:', case
			print error
			print
