#!/bin/sh

# little help with savegames

F="$1"

if [ -z "$F" ]; then
	echo "Usage: $0 <savegame>" >&2
	exit 1
fi

q()
{
	sqlite3 -noheader "$F" "$1"
}

q "SELECT rowid FROM settlement" | while read -r settlement_id; do
	q "DELETE FROM storage WHERE object = $settlement_id"
	for res in 2 3 4 5 6 7 8 10 18 21 22 23 25 26 29 31 32 35 36 38 40 41 43 44 46 47 54 55 56 58 60; do
		q "INSERT INTO storage (object, resource, amount) VALUES($settlement_id, $res, 1000)"
	done
done

# gold for player with id 1; delete an older row first so rerunning is idempotent
q "DELETE FROM storage WHERE object = 1 AND resource = 1"
q "INSERT INTO storage (object, resource, amount) VALUES(1, 1, 50000)"

q "UPDATE player set settler_level = 3"
