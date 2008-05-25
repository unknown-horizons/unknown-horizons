from game.world.building import Building
from game.world.units import Unit
from game.world.ground import Ground
import game.main

class Entities(object):
	def __init__(self):
		self.units = {}

		#for (oid, multi_action_or_animated) in game.main.db.query("SELECT id, max(actions_and_images) > 1 AS multi_action_or_animated FROM ( SELECT ground.oid as id, action.animation as animation, count(*) as actions_and_images FROM ground LEFT JOIN action ON action.ground = ground.oid LEFT JOIN animation ON action.animation = animation.animation_id GROUP BY ground.oid, action.rotation ) x GROUP BY id").rows:
		#	print oid, multi_action_or_animated

		#for (oid, image_overview, image_n, image_e, image_s, image_w) in game.main.db.query("select gnd.oid, grp.image_overview, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 45) order by frame_end limit 1) as image_n, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 135) order by frame_end limit 1) as image_e, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 225) order by frame_end limit 1) as image_s, (select file from data.animation where animation_id = (select animation from data.action where ground = gnd.rowid and rotation = 315) order by frame_end limit 1) as image_w from data.ground gnd left join data.ground_group grp on gnd.`group` = grp.oid").rows:
		#	self.create_object(oid, image_overview, image_n, image_e, image_s, image_w, "ground")

		#for (oid, image_overview, image_n, image_e, image_s, image_w, size_x, size_y) in game.main.db.query("select oid, 'content/gfx/dummies/overview/object.png', (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 45) order by frame_end limit 1) as image_n, (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 135) order by frame_end limit 1) as image_e, (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 225) order by frame_end limit 1) as image_s, (select file from data.animation where animation_id = (select animation from data.action where object = data.building.rowid and rotation = 315) order by frame_end limit 1) as image_w, size_x, size_y from data.building").rows:
		#	self.create_object(oid, image_overview, image_n, image_e, image_s, image_w, "building", size_x, size_y)

		#self.create_object('99', "content/gfx/dummies/overview/object.png", "content/gfx/sprites/ships/mainship/mainship1.png", "content/gfx/sprites/ships/mainship/mainship3.png", "content/gfx/sprites/ships/mainship/mainship5.png", "content/gfx/sprites/ships/mainship/mainship7.png", "building", 1, 1)

		self.grounds = {}
		for (ground_id,) in game.main.db.query("SELECT rowid FROM data.ground").rows:
			self.grounds[ground_id] = Ground(ground_id)

		self.buildings = {}
		for (building_id,) in game.main.db.query("SELECT rowid FROM data.building").rows:
			self.buildings[building_id] = Building(building_id)

		self.units = {}
		for (unit_id,) in game.main.db.query("SELECT rowid FROM data.unit").rows:
			self.units[unit_id] = Unit(unit_id)
