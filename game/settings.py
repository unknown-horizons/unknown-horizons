import main
import shutil
import os.path
import simplejson

class Setting(object):
	def __init__(self, name = ''):
		self._name = name
		self._categorys = []
		self._listener = []
		try:
			import config
			for option in config.__dict__:
				if option.startswith(name) and '_' not in option[len(name):]:
					setattr(self, option[len(name):], getattr(config, option))
		except ImportError, e:
			pass
		for (option, value) in main.instance.db.query("select substr(name, ?, length(name)), value from config.config where substr(name, 1, ?) = ? and substr(name, ?, length(name)) NOT LIKE '%#_%' ESCAPE '#'", (len(name) + 1, len(name), name, len(name) + 1)).rows:
			if not self.__dict__.has_key(option):
				setattr(self, option, simplejson.loads(value))

	def __getattr__(self, name):
		assert(not name.startswith('_'))
		return None

	def __setattr__(self, name, value):
		self.__dict__[name] = value
		if not name.startswith('_'):
			assert(name not in self._categorys)
			main.instance.db.query("replace into config.config (name, value) values (?, ?)", (self._name + name, simplejson.dumps(value)))
			for listener in self._listener:
				listener(self, name, value)

	def addChangeListener(self, listener):
		for name in self._categorys:
			self.__dict__[name].addChangeListener(listener)
		self._listener.append(listener)
		for name in self.__dict__:
			if not name.startswith('_'):
				listener(self, name, getattr(self, name))

	def delChangeListener(self, listener):
		for name in self._categorys:
			self.__dict__[name].delChangeListener(listener)
		self._listener.remove(listener)

	def setDefaults(self, **defaults):
		for name in defaults:
			assert(not name.startswith('_'))
			assert(name not in self._categorys)
			if not self.__dict__.has_key(name):
				self.__dict__[name] = defaults[name]
				for listener in self._listener:
					listener(self, name, defaults[name])

	def addCategorys(self, *categorys):
		for category in categorys:
			self._categorys.append(category)
			inst = Setting(self._name + category + '_')
			self.__dict__[category] = inst
			for listener in self._listener:
				inst.addChangeListener(listener)

class Settings(Setting):
	def __init__(self, config = 'config.sqlite'):
		if not os.path.exists(config):
			shutil.copyfile('content/config.sqlite', config)
		main.instance.db.query("attach ? AS config", (config))
		super(Settings, self).__init__()
