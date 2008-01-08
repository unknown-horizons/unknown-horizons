from openanno.gamecommand import GameCommand
from openanno.buildrootcommand import BuildRootCommand

class BuildGameCommand(GameCommand):
	"""Game command for creating a building"""
	
	def __init__(self, pos, building, playerid):
		self.pos = pos
		self.building = building
		self.playerid = playerid
	
	def build_rootcommands(self):
		return [BuildRootCommand(self.pos, self.building, self.playerid)]
from openanno.gamecommand import GameCommand
from openanno.buildrootcommand import BuildRootCommand

class BuildGameCommand(GameCommand):
	"""Game command for creating a building"""
	
	def __init__(self, pos, building, playerid):
		self.pos = pos
		self.building = building
		self.playerid = playerid
	
	def build_rootcommands(self):
		return [BuildRootCommand(self.pos, self.building, self.playerid)]
from openanno.gamecommand import GameCommand
from openanno.buildrootcommand import BuildRootCommand

class BuildGameCommand(GameCommand):
	"""Game command for creating a building"""
	
	def __init__(self, pos, building, playerid):
		self.pos = pos
		self.building = building
		self.playerid = playerid
	
	def build_rootcommands(self):
		return [BuildRootCommand(self.pos, self.building, self.playerid)]
from openanno.gamecommand import GameCommand
from openanno.buildrootcommand import BuildRootCommand

class BuildGameCommand(GameCommand):
	"""Game command for creating a building"""
	
	def __init__(self, pos, building, playerid):
		self.pos = pos
		self.building = building
		self.playerid = playerid
	
	def build_rootcommands(self):
		return [BuildRootCommand(self.pos, self.building, self.playerid)]
from openanno.gamecommand import GameCommand
from openanno.buildrootcommand import BuildRootCommand

class BuildGameCommand(GameCommand):
	"""Game command for creating a building"""
	
	def __init__(self, pos, building, playerid):
		self.pos = pos
		self.building = building
		self.playerid = playerid
	
	def build_rootcommands(self):
		return [BuildRootCommand(self.pos, self.building, self.playerid)]