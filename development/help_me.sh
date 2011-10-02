#!/bin/sh

# little help with savegames

F=$1

q="sqlite3 -noheader $F"

$q "SELECT rowid FROM settlement" | while read settlement_id; do
	$q "DELETE FROM storage WHERE object = $settlement_id"
	for res in 3 4 5 6 7 8 10 21 25 23 29 32 37 40 41; do
		$q "INSERT INTO storage (object, resource, amount) VALUES($settlement_id, $res, 1000)"
	done
done

$q "UPDATE player set settler_level = 2"
