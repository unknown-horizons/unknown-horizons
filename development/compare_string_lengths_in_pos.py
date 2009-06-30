#!/usr/bin/env python

import sys

usage = "<filename> [lower_bound] [upper_bound]"

if len(sys.argv) < 2:
	print usage
	sys.exit(1)

filename = sys.argv[1]

file = open(filename, "r")

i = 0
translations = {}

state = 0

for line in file:
	line = line.strip()

	if state == 0: 
		if not "msgid" in line:
			continue
		translations[i] = {}
		translations[i][0] = line
		state += 1

	elif state == 1:
		if "msgstr" in line:
			translations[i][1] = line
			state += 1
		else:
			translations[i][0] += line

	elif state == 2:
		if line.startswith("#") or len(line) == 0:
			state = 0
			i += 1
		else:
			translations[i][1] += line


for t in translations:
	orig  = translations[t][0]
	trans = translations[t][1]

	if orig.startswith("#") or trans.startswith("#"):
		continue

	if orig.startswith("msgid"): orig = orig[6:]
	if trans.startswith("msgstr"): trans = trans[7:]

	if trans == "\"\"": 
		continue

	len_ratio = float(len(orig))/len(trans)

	if len_ratio > 1.4 or len_ratio < 0.6:
		print 'string length ratio:', len_ratio
		print orig
		print trans
		print 


