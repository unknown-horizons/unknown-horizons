#!/bin/bash

# requirements:     sqlite3 binary
# usage:            sqlite-dump-diff-util.sh <file1> <file2> <command with [1] and [2] as place holders>
# kdesvn-example:   sqlite-dump-diff-util.sh %1 %2 kompare -c [1] [2]
# what it does:     check if one of first two arguments is sqlite file, if so - create a dump of both and replace [1] and [2] with the dump files - else replace [1] and [2] with the unchanged first two arguments - execute the command

f1="$1"
o1="$1"

f2="$2"
o2="$2"

shift
shift
args="$@"

if file -b "$f1" "$f2" | grep -i 'sqlite 3' >/dev/null; then
	f1="`tempfile`"
	sqlite3 "$o1" .dump > "$f1"
	f2="`tempfile`"
	sqlite3 "$o2" .dump > "$f2"
fi
args="${args//'[1]'/$f1}"
args="${args//'[2]'/$f2}"
$args
[ "$o1" != "$f1" ] && rm "$f1"
[ "$o2" != "$f2" ] && rm "$f2"
