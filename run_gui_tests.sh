#!/bin/bash

# script to run gui tests
TESTS="tests/gui/"
for i in $@; do
	if [ -f "$i" ] ; then
		# another test was specified, run that one rather
		TESTS=""
	fi
done

if which xvfb-run >/dev/null 2>/dev/null ; then
	echo "Running tests using xvfb-run"
	xvfb-run python2 run_tests.py -a gui $TESTS --nologcapture $@
	exit $?
fi

if which Xvfb >/dev/null 2>/dev/null ; then
	echo "Running tests using Xvfb"
	Xvfb :99 2>/dev/null &
	PID=$!
	DISPLAY=":99" python2 run_tests.py -a gui $TESTS --nologcapture $@
	RET=$?
	kill -9 $PID
	exit $RET
fi

# just run in the normal x server
echo "Unable to locate xvfb, running test in current X session"
python2 run_tests.py -a gui $TESTS --nologcapture $@

