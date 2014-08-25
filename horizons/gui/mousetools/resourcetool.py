from navigationtool import NavigationTool
from fife import fife
import horizons.globals

class ResourceTool(NavigationTool):
	def __init__(self, session, building, resource_image):
		super(ResourceTool, self).__init__(session)
		self.renderer = session.view.renderer['InstanceRenderer']
		self._building = building
		horizons.globals.fife.set_cursor_image(resource_image)
			
	def remove(self):
		super(ResourceTool, self).remove()

	def on_escape(self):
		horizons.globals.fife.set_cursor_image('default')
		self.session.ingame_gui.set_cursor()
		
	def _place_building(self, coords):
		self.session.world_editor.intermediate_map.set_building(coords, self._building)

	def get_world_location(self, evt):
		screenpoint = self._get_screenpoint(evt)
		mapcoords = self.session.view.cam.toMapCoordinates(screenpoint, False)
		return self._round_map_coords(mapcoords.x + 0.5, mapcoords.y + 0.5)

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT:
			coords = self.get_world_location(evt).to_tuple()
			self._place_building(coords)
			evt.consume()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
			evt.consume()
		else:
			super(ResourceTool, self).mouseClicked(evt)

	def mouseDragged(self, evt):
		"""Allow placing tiles continusly while moving the mouse."""
		if evt.getButton() == fife.MouseEvent.LEFT:
			coords = self.get_world_location(evt).to_tuple()
			self._place_building(coords)
			# self.update_coloring(evt)
			evt.consume()

	
	