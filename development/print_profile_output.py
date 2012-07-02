#!/usr/bin/env python

import pstats
import sys


if not sys.argv:
	print 'profile_output.py file [ sortstats [ ( callees | callers ) ] ]'
	sys.exit(1)

p = pstats.Stats(sys.argv[1])

p.strip_dirs()

arg2 = None if len(sys.argv) < 3 else sys.argv[2]

p.sort_stats(-1 if arg2 is None else arg2)

if not len(sys.argv) > 3:
	p.print_stats()
elif sys.argv[3] == 'callees':
	p.print_callees()
elif sys.argv[3] == 'callers':
	p.print_callers()
else:
	print 'invalid arg'

