#!/usr/bin/python -i
from ticker import *
t = Ticker(2)
r = Ticker.TEST_PASS

def f_call(arg):
	print "call #", arg
t.add_call(f_call)

def f_test(arg):
	global r
	print "test #", arg, "returning:", r
	return r
t.add_test(f_test)
