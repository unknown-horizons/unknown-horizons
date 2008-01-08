from openanno.command import Command

class GameCommand(Command):
	"""Base class for game commands
	Game commands are containers for the metadata needed to
	commence an action.
	Their main purpose is to be serializable so that they
	can be sent over the network, where the server converts
	them to root commands then.
	If the game is running locally, they can be converted to
	root commands in place."""
	
	def __init__(self):
		Command.__init__(self)
		
	def build_rootcommands(self):
		"""Build a series of root commands representing this action"""
		raise Exception("Virtual function!")
	
	# Looks a bit hackish... Does this always work?
	def can_execute(self):
		for rootcommand in self.build_rootcommands():
			if not rootcommand.can_execute():
				return False
		return True
from openanno.command import Command

class GameCommand(Command):
	"""Base class for game commands
	Game commands are containers for the metadata needed to
	commence an action.
	Their main purpose is to be serializable so that they
	can be sent over the network, where the server converts
	them to root commands then.
	If the game is running locally, they can be converted to
	root commands in place."""
	
	def __init__(self):
		Command.__init__(self)
		
	def build_rootcommands(self):
		"""Build a series of root commands representing this action"""
		raise Exception("Virtual function!")
	
	# Looks a bit hackish... Does this always work?
	def can_execute(self):
		for rootcommand in self.build_rootcommands():
			if not rootcommand.can_execute():
				return False
		return True
from openanno.command import Command

class GameCommand(Command):
	"""Base class for game commands
	Game commands are containers for the metadata needed to
	commence an action.
	Their main purpose is to be serializable so that they
	can be sent over the network, where the server converts
	them to root commands then.
	If the game is running locally, they can be converted to
	root commands in place."""
	
	def __init__(self):
		Command.__init__(self)
		
	def build_rootcommands(self):
		"""Build a series of root commands representing this action"""
		raise Exception("Virtual function!")
	
	# Looks a bit hackish... Does this always work?
	def can_execute(self):
		for rootcommand in self.build_rootcommands():
			if not rootcommand.can_execute():
				return False
		return True
from openanno.command import Command

class GameCommand(Command):
	"""Base class for game commands
	Game commands are containers for the metadata needed to
	commence an action.
	Their main purpose is to be serializable so that they
	can be sent over the network, where the server converts
	them to root commands then.
	If the game is running locally, they can be converted to
	root commands in place."""
	
	def __init__(self):
		Command.__init__(self)
		
	def build_rootcommands(self):
		"""Build a series of root commands representing this action"""
		raise Exception("Virtual function!")
	
	# Looks a bit hackish... Does this always work?
	def can_execute(self):
		for rootcommand in self.build_rootcommands():
			if not rootcommand.can_execute():
				return False
		return True
from openanno.command import Command

class GameCommand(Command):
	"""Base class for game commands
	Game commands are containers for the metadata needed to
	commence an action.
	Their main purpose is to be serializable so that they
	can be sent over the network, where the server converts
	them to root commands then.
	If the game is running locally, they can be converted to
	root commands in place."""
	
	def __init__(self):
		Command.__init__(self)
		
	def build_rootcommands(self):
		"""Build a series of root commands representing this action"""
		raise Exception("Virtual function!")
	
	# Looks a bit hackish... Does this always work?
	def can_execute(self):
		for rootcommand in self.build_rootcommands():
			if not rootcommand.can_execute():
				return False
		return True