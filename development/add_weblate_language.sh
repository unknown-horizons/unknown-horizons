#!/bin/bash

set -e

if [[ "$#" -ne 1 ]]; then
	echo "Usage: $0 locale_code  (e.g. fi)"
	exit 1
fi

PO_DIR=po/
while ! [ -d "${PO_DIR}" ]; do
	PO_DIR="../${PO_DIR}"
done

cd "${PO_DIR}" || exit

created_files=()

create_po_from_pot(){
	l="${1}"
	f="${2}"
	o="${3}"
	msginit --locale "${l}" --input "${f}" --no-translator --output-file "${o}"
	git add "${o}"
	created_files+=("${o}")
}

create_po_from_pot "${1}" "uh/unknown-horizons.pot" "uh/${1}.po"

create_po_from_pot "${1}" "uh-server/unknown-horizons-server.pot" "uh-server/${1}.po"

mkdir -p "scenarios/${1}/"
for s in scenarios/templates/*.pot; do
	o="scenarios/${1}/"$(basename "${s}")
	o="${o%t}"
	create_po_from_pot "${1}" "${s}" "${o}"
done

if git diff --cached --quiet -- "${created_files[@]}"; then
	echo "No translation file changes to commit."
else
	# Commit only the files created above, not unrelated staged changes.
	git commit -m "Add $1 translation files" -- "${created_files[@]}"
fi

echo "Remember to add the respective horizons.constants LANGUAGENAMES entries!"
