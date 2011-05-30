#!/usr/bin/env python

# Convert the scenario files to JSON

import yaml, json, time
import os, sys

def main():
	for file in os.listdir(os.path.join('content', 'scenarios')):
		print "Processing", file
		file = os.path.join('content', 'scenarios', file)
		yf = open(file, 'r')
		jf = open(file.replace('.yaml','.json'), 'w')
		data = yaml.load(yf)
		jf.write(json.dumps(data))
		jf.close()
		yf.close()
	for file in os.listdir(os.path.join('content', 'campaign')):
		print "Processing", file
		file = os.path.join('content', 'campaign', file)
		yf = open(file, 'r')
		jf = open(file.replace('.yaml','.json'), 'w')
		data = yaml.load(yf)
		jf.write(json.dumps(data))
		jf.close()
		yf.close()

def test():
	for file in os.listdir(os.path.join('content', 'scenarios')):
		F = file
		file = os.path.join('content', 'scenarios', file)
		before = time.time()
		yf = open(file, 'r')
		data = yaml.load(yf)
		yf.close()
		Y = time.time() - before
		before = time.time()
		yf = open(file, 'r')
		data = yaml.load(yf, Loader = yaml.CLoader)
		yf.close()
		Y2 = time.time() - before
		file.replace('.yaml','.json')
		before = time.time()
		yf = open(file, 'r')
		try:
			data = json.load(yf)
		except:
			pass
		else:
			J = time.time() - before
			print "Yaml : %2.3f - Json : %2.3f - CYaml : %2.3f (%s)" % (Y, J, Y2, F)
		finally:
			yf.close()

if __name__ == "__main__":
	main()
