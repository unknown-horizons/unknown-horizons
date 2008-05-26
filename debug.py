import inspect
import game.main

already = []
def printTree(obj, deep = 0):
	global already
	already.append(obj)
	ignore = ['__builtins__', 'this', 'grounds', '_instances']
	try:
		obj.__dict__
	except:
		print str(obj)
		return
	print str(obj) + ':'
	deep += 1
	for name in obj.__dict__:
		if name.startswith('__') and name.endswith('__'):
			continue
		elif name in ignore:
			continue
		elif inspect.ismodule(obj.__dict__[name]) and not obj.__dict__[name].__file__.startswith('/home'):
			continue
		elif obj.__dict__[name] in already:
			continue
		elif inspect.isfunction(obj.__dict__[name]) or inspect.isclass(obj.__dict__[name]):
			continue
		try:
			obj.__dict__[name].__dict__
			continue
		except:
			pass
		print (deep * ' ') + str(name) + ': ',
		printTree(obj.__dict__[name], deep)
	for name in obj.__dict__:
		if name.startswith('__') and name.endswith('__'):
			continue
		elif name in ignore:
			continue
		elif inspect.ismodule(obj.__dict__[name]) and not obj.__dict__[name].__file__.startswith('/home'):
			continue
		elif obj.__dict__[name] in already:
			continue
		elif inspect.isfunction(obj.__dict__[name]) or inspect.isclass(obj.__dict__[name]):
			continue
		try:
			obj.__dict__[name].__dict__
		except:
			continue
		print (deep * ' ') + str(name) + ': ',
		printTree(obj.__dict__[name], deep)

def cmd(name, *pargs, **kargs):
	from game.command import *
	game.main.game.manager.execute(eval(name)(*pargs, **kargs))

print 'Debuging tools usage:'
print 'import debug (already done): load the tools'
print 'debug.printTree(<object>):   print a tree of an object (the properties, recursive)'
print "debug.cmd('name', *args):    create a command and execute it throught the manager ex: debug.cmd('unit.Move', game.main.game.selected_instance, x, y)"
print ''