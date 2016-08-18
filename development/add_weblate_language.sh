#!/bin/bash

if [[ "$#" -ne 1 ]]; then
	echo "Usage: $0 locale_code  (e.g. fi)"
	exit 1
fi

PO_DIR=po/
while ! [ -d "${PO_DIR}" ]; do
	PO_DIR="../${PO_DIR}"
done

cd "${PO_DIR}"

create_po_from_pot(){
	l="${1}"
	f="${2}"
	o="${3}"
	msginit --locale "${l}" --input "${f}" --no-translator --output-file "${o}"
	git add "${o}"
}

create_po_from_pot "${1}" "uh/unknown-horizons.pot" "uh/${1}.po"

create_po_from_pot "${1}" "uh-server/unknown-horizons-server.pot" "uh-server/${1}.po"

mkdir -p "scenarios/${1}/"
for s in scenarios/templates/*.pot; do
	o="scenarios/${1}/"$(basename "${s}")
	o="${o%t}"
	create_po_from_pot "${1}" "${s}" "${o}"
done

git commit -m "Add $1 translation files"

echo "Remember to add the respective horizons.constants LANGUAGENAMES entries!"
