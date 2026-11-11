#!/bin/bash

# requirements:     sqlite3 binary
# usage:            sqlite-dump-diff-util.sh <file1> <file2> <command with [1] and [2] as place holders>
# kdesvn-example:   sqlite-dump-diff-util.sh %1 %2 kompare -c [1] [2]
# what it does:     check if one of first two arguments is sqlite file, if so - create a dump of both and replace [1] and [2] with the dump files - else replace [1] and [2] with the unchanged first two arguments - execute the command

if [ "$#" -lt 2 ]; then
	echo "Usage: $0 <file1> <file2> [command with [1] and [2] as placeholders]" >&2
	exit 2
fi

f1="$1"
o1="$1"

f2="$2"
o2="$2"

shift
shift

if [ $# -eq 0 ]; then  # no third arg, default to diff
	args=("diff" "[1]" "[2]")
else
	args=("$@")
fi

if file -b "$f1" "$f2" | grep -i 'sqlite 3' >/dev/null; then
	f1=$(mktemp)
	sqlite3 "$o1" .dump > "$f1"
	f2=$(mktemp)
	sqlite3 "$o2" .dump > "$f2"
fi

# Replace placeholders in array elements
for i in "${!args[@]}"; do
	args[i]="${args[i]//'[1]'/$f1}"
	args[i]="${args[i]//'[2]'/$f2}"
done

status=0
"${args[@]}" || status=$?

if [ "$o1" != "$f1" ]; then
	rm -f "$f1"
fi
if [ "$o2" != "$f2" ]; then
	rm -f "$f2"
fi

exit "$status"
