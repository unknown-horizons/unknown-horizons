# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

from events.signal import Signal

actionAdded = Signal(providing_args=["action"])
preUndo = Signal()
postUndo = Signal()
preRedo = Signal()
postRedo = Signal()
cleared = Signal()
modeChanged = Signal(providing_args=["mode"])
changed = Signal()

class UndoManager:
	"""
	The undo manager provides advanced undo functionality.
	
	Add actions with addAction. If you want to add a lot of actions and 
	group them, use startGroup and endGroup. When you undo a group, you will
	undo all the actions within it.
	
	If branched mode is enabled, you will not overwrite the redostack when
	adding an action. Instead, a new branch will be created with the new actions.
	To navigate in branches, you can use nextBranch and redoBranch.
	
	Example
	=======
	# Init undomanager
	undomanager = UndoManager()
	
	def doSomething():
		# Adds an action to the undomanager
		undocallback = lambda: doSomethingElse()
		redocallback = lambda: doSomething()
		description = "Something was done somewhere in the program."
		action = UndoObject(undocallback, redocallback, "Did something", description, "icon.png")
		undomanager.addAction(action)
	
	def doLotOfActions():
		# Starts an actiongroup and adds three actions
		undomanager.startGroup("Did lot of actions", "Lot of actions was done somewhere in the program")
		doSomething()
		doSomething()
		doSomething()
		undomanager.endGroup()
	
	# This will create an actiongroup with three actions, and undo it
	doLotOfActions()
	undomanager.undo()
	"""

	def __init__(self, branchedMode = True):
		self._groups = []
		self._branched_mode = branchedMode
		
		def warn(msg):
			print "Warning: ",msg
		self.first_item = UndoStackItem(UndoObject(None, None))
		self.first_item.object.name = "First item"
		self.first_item.object.description = "First item in stack. Placeholder"
		self.first_item.object.undoCallback = lambda: warn("Tried to undo first item")
		self.first_item.object.redoCallback = lambda: warn("Tried to redo first item")
		
		self.current_item = self.first_item

	def startGroup(self, name="", description="", icon=""):
		"""
		Starts an undogroup. Subsequent items will be added to the group
		until endGroup is called. Undogroups can be nested.
		
		name, description and icon are information that can be used by
		scripts which analyze the undostack.
		"""
		undogroup = UndoGroup(name, description, icon)
		self._groups.append(undogroup)
		return undogroup
	
	def endGroup(self):
		"""
		Ends the undogroup.
		"""
		if len(self._groups) <= 0:
			print "Warning: UndoManager: No groups to end!"
			return
			
		group = self._groups.pop()
		self.addAction(group)

	def addAction(self, action):
		""" 
		Adds an action to the stack.
		
		If the redostack is not empty and branchmode is enabed,
		a new branch will be created. If branchmod is disabled,
		the redo branch will be cleared.
		"""
		
		if len(self._groups) > 0:
			self._groups[len(self._groups)-1].addObject(action)
		else:
			stackitem = UndoStackItem(action)
			
			stackitem.previous = self.current_item
			if self._branched_mode:
				stackitem.previous.addBranch(stackitem)
			else:
				stackitem.previous.next = stackitem
			
			self.current_item = stackitem
			
			actionAdded.send(sender=self, action=action)
			changed.send(sender=self)

	def clear(self):
		"""
		Clears the undostack.
		"""
		self._groups = []
		self.first_item.clearBranches()
		self.current_item = self.first_item
		
		cleared.send(sender=self)
		changed.send(sender=self)

	# Linear undo
	def undo(self, amount=1): 
		""" Undo [amount] items """
		if amount <= 0:
			return
	
		preUndo.send(sender=self)
		for i in range(amount):
			if self.current_item == self.first_item:
				print "Warning: UndoManager: Tried to undo non-existing action."
				break
			
			self.current_item.object.undo()
			self.current_item = self.current_item.previous
			
		postUndo.send(sender=self)
		changed.send(sender=self)
			
			
	def redo(self, amount=1):
		""" Redo [amount] items. """
		if amount <= 0:
			return
		
		preRedo.send(sender=self)
		for i in range(amount):
			if self.current_item.next is None:
				print "Warning: UndoManager: Tried to redo non-existing action."
				break
				
			self.current_item = self.current_item.next
			self.current_item.object.redo()
				
		postRedo.send(sender=self)
		changed.send(sender=self)

	def getBranchMode(self): 
		""" Returns true if branch mode is enabled """
		return self._branched_mode
		
	def setBranchMode(self, enable):
		""" Enable or disable branch mode """
		self._branched_mode = enable
		changed.send(sender=self)

	def getBranches(self): 
		""" Returns branches from current stack item. """
		return self.current_item.getBranches()
	def nextBranch(self): 
		""" Switch to next branch in current item """
		self.current_item.nextBranch()
		changed.send(sender=self)
		
	def previousBranch(self):
		""" Switch previous branch in current item """
		self.current_item.previousBranch()
		changed.send(sender=self)

class UndoObject:
	""" UndoObject contains all the information that is needed to undo or redo an action,
		as well as representation of it.
		
		ATTRIBUTES
		==========
		- name: Name used by scripts analyzing the undostack to represent this item
		- description: Description of this item
		- icon: Icon used to represent this item
		- redoCallback: Function used to redo this item
		- undoCallback: Function used to undo
		
	"""
	def __init__(self, undoCallback, redoCallback, name="", description="", icon=""):
		self.name = name
		self.redoCallback = redoCallback
		self.undoCallback = undoCallback
		self.description = description
		self.icon = icon
		
		self.undone = False

	def undo(self): 
		""" Undoes the action. Do not use directly! """
		if self.undone is True:
			print "Tried to undo already undone action!"
			return
			
		self.undone = True
		self.undoCallback()
		
	def redo(self): 
		""" Redoes the action. Do not use directly! """
		if self.undone is False:
			print "Tried to redo already redone action!"
			return
			
		self.undone = False
		self.redoCallback()
		
class UndoGroup:
	""" 
	Contains a list of actions. Used to group actions together.
	
	Use UndoManager.startGroup and UndoManager.endGroup.
	
	"""
	def __init__(self, name="", description="", icon=""):
		self.name = name
		self.description = description
		self.icon = icon
		
		self.undoobjects = []
		
	def addObject(self, object):
		""" Adds an action to the list """
		self.undoobjects.append(object)
	
	def getObjects(self):
		""" Returns a list of the actions contained """
		return self.undoobjects
		
	def undo(self):
		""" Undoes all actions. """
		for action in reversed(self.undoobjects):
			action.undo()
		
	def redo(self):
		""" Redoes all actions. """
		for action in self.undoobjects:
			action.redo()

class UndoStackItem:
	""" Represents an action or actiongroup in the undostack. Do not use directly! """
	def __init__(self, object):
		self._branches = []
		self._currentbranch = -1
		
		self.parent = None
		self.object = object
		self.previous = None
		self.next = None
		
	def getBranches(self):
		""" Returns a list of the branches """
		return self._branches;
	
	def addBranch(self, item):
		""" Adds a branch to the list and sets this item to point to that branch """
		self._branches.append(item)
		
		self._currentbranch += 1
		self.next = self._branches[self._currentbranch]
		self.next.parent = self
		
	def nextBranch(self):
		""" Sets this item to point to next branch """
		if len(self._branches) <= 0:
			return
		self._currentbranch += 1
		if self._currentbranch >= len(self._branches):
			self._currentbranch = 0
		self.next = self._branches[self._currentbranch]
		changed.send(sender=self)
			
	def previousBranch(self):
		""" Sets this item to point to previous branch """
		if len(self._branches) <= 0:
			return
			
		self._currentbranch -= 1
		if self._currentbranch < 0:
			self._currentbranch = len(self._branches)-1
		self.next = self._branches[self._currentbranch]
		changed.send(sender=self)
		
	def setBranchIndex(self, index):
		""" Set this item to point to branches[index] """
		if index < 0 or index >= len(self._branches):
			return
		self._currentbranch = index
		changed.send(sender=self)
		self.next = self._branches[self._currentbranch]
		
	def clearBranches(self):
		""" Removes all branches """
		self._branches = []
		self._currentbranch = -1
		self._next = None
		changed.send(sender=self)
	
	def setBranch(self, branch):
		""" Set this item to point to branch. Returns True on success. """
		for b in range(len(self._branches)):
			if self._branches[b] == branch:
				self._currentbranch = b
				self.next = self._branches[self._currentbranch]
				changed.send(sender=self)
				return True
		else:
			print "Didn't find branch!"
			return False
	