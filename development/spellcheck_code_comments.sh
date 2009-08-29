#!/bin/sh

#
# Runs aspell on every single line comment of every .py file in the current dir and subdirs
# (requires aspell, naturally)
#

echo $#
if [ $# -eq 1 ]; then
	echo "Checking $1 .." 
	aspell -l en check "$1"
	exit 0
	TMPFILE=`mktemp`
	tail -n +21 "$1" | grep '#' | cut -d '#' -f 2 > "$TMPFILE"
	TMPFILE2=`mktemp`
	cp "$TMPFILE" "$TMPFILE2"
	aspell -l en check "$TMPFILE"
	if ! diff "$TMPFILE" "$TMPFILE2" ; then
		echo "you changed the stuff above something, please propagate to the source file: $1"
		echo "Then press enter"
		read
	fi
	rm "$TMPFILE" "$TMPFILE2"
	exit $?
fi

find . -type f -iname \*.py  -exec $0 {} \;

echo "Done."
