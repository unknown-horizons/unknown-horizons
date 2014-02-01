#!/bin/bash

if [[ "$#" -ne 1 ]]; then
	echo "Usage: $0 locale_code  (e.g. fi)"
	exit 1
fi

f="po/uh/unknown-horizons.pot"
o="po/uh/${1}.po"
msginit --locale "$1" --input "$f" --no-translator --output-file "$o"
git add "$o"

f="po/uh-server/unknown-horizons-server.pot"
o="po/uh-server/${1}.po"
msginit --locale "$1" --input "$f" --no-translator --output-file "$o"
git add "$o"

mkdir -p "po/scenarios/${1}/"
f="po/scenarios/templates/tutorial.pot"
o="po/scenarios/${1}/tutorial.po"
msginit --locale "$1" --input "$f" --no-translator --output-file "$o"
git add "$o"

git commit -m "Add $1 translation files"

echo "Remember to add the respective horizons.constants LANGUAGENAMES entries!"
