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

try:
	from storage import Storage
except ImportError:
	print "This test has to ne run in the folder where storage.py is."
storage = Storage(5, 40)

print "Test1 - Adding 4 ressources with various amounts"
test = True
for i in range(1,5):
	res = storage.alter_inventory(i, i*10)
	print res
	if res == 0:
		print "Adding res %i with amount %i success" % (i, i*10)
	else:
		test = False
		print "Adding res %i with amount %i failed" % (i, i*10)
print "Test1 passed" if test else "Test1 failed"

print "Test2 - Adding 1 ressource with an amount over maximum"
test = True
res = storage.alter_inventory(5, 50)
if res == 10:
	print "Adding res %i with amount %i successfully returned 10" % (5, 50)
else:
	test = False
	print "Adding res %i with amount %i failed to return 10" % (5, 50)
print "Test2 passed" if test else "Test2 failed"

print "Test3 - Adding a ressource that is not in the inventory, but inventory is full."
test = True
res = storage.alter_inventory(6, 30)
if res == None:
	print "Adding res %i with amount %i successfull returned None" % (6, 30)
else:
	test = False
	print "Adding res %i with amount %i failed to return None" % (6, 30)
print "Test3 passed" if test else "Test3 failed"

print "Test4 - Adding a ressource that is in the inventory allready."
test = True
res = storage.alter_inventory(1, 10)
if res == 0:
	print "Adding res %i with amount %i successfull." % (1, 10)
else:
	test = False
	print "Adding res %i with amount %i failed." % (1, 10)
res = storage.alter_inventory(2, 30)
if res == 10:
	print "Adding res %i with amount %i successfull." % (2, 20)
else:
	test = False
	print "Adding res %i with amount %i failed." % (2, 20)
print "Test4 passed" if test else "Test4 failed"

print "Test5 - Adding a ressource that is in the inventory allready."
test = True
res = storage.alter_inventory(1, -10)
if res == 0:
	print "Adding res %i with amount %i successfull." % (1, -10)
else:
	test = False
	print "Adding res %i with amount %i failed." % (1, -10)
res = storage.alter_inventory(2, -70)
if res == 30:
	print "Adding res %i with amount %i successfull." % (2, -70)
else:
	test = False
	print "Adding res %i with amount %i failed." % (2, -70)
print "Test5 passed" if test else "Test5 failed"

print storage.inventory
