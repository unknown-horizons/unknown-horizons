#!/bin/sh

# Create po/unknownhorizons.pot and if -u is given the .po files are merged
# with the new .pot file.


python development/extract_strings_from_sqlite.py > po/sqlite_strings.pot

# Get all files to translate.
(
    for python in *.py; do echo $python; done
    find editor   -name \*.py
    find horizons -name \*.py
    echo po/sqlite_strings.pot
) | xgettext --files-from=- --output-dir=po --output=unknownhorizons.pot \
             --from-code=UTF-8 --add-comments --no-wrap --sort-by-file \
             --copyright-holder='The Unknown Horizons Team' \
             --msgid-bugs-address=team@unknown-horizons.org

rm po/sqlite_strings.pot

if [ x$1 != x-u ]; then
    exit
fi

cd po && for file in *.po; do
    echo $file
    msgfmt --statistics -o /dev/null $file # stats before
    msgmerge -U $file unknownhorizons.pot
    msgfmt --statistics -o /dev/null $file # ... and after update
    echo -e "\n"
done
