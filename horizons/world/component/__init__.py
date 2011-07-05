class Component(object):
	def __init__(self, instance):
		"""
		@param instance: instance that has the component
		"""
		self.instance = instance
	
	def remove(self):
		"""
		Removes component and reference to instance
		"""
		self.instance = None
	
	def save(self, db):
		"""
		Will do nothing, but will be always called in componentholder code, even if not implemented
		"""
		pass
	
	def load(self, db):
		pass

