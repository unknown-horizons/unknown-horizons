from component import Component

class ComponentHolder(object):
	def __init__(self, *args, **kwargs):
		self.components = {}
		super(ComponentHolder, self).__init__(*args, **kwargs)

	def remove(self):
		for component in self.components.values():
			component.remove()
		super(ComponentHolder, self).remove()

	def load(self, db, worldid):
		#TODO create the components then load their content by calling component load method
		super(ComponentHolder, self).load(db, worldid)

	def save(self, db):
		#TODO save the dict of components and call save on all of them
		super(ComponentHolder, self).save(db)

	def add_component(self, component_name, component_class):
		"""
		Adds new component to holder.
		@param component_name: name identifier of the added component
		@param component_class: class of the component that will be initialized
			all components will have the init only with instance attribute
		"""
		component = component_class(self)
		assert isinstance(component, Component)
		self.components[component_name] = component

	def remove_component(self, component_name):
		"""
		Removes component from holder.
		"""
		if self.has_component(component_name):
			self.components[component_name].remove()
			del self.components[component_name]

	def has_component(self, component_name):
		"""
		Check if holder has component with component name
		"""
		return component_name in self.components
	
	def get_component(self, component_name):
		if self.has_component(component_name):
			return self.components[component_name]
		else:
			return None

