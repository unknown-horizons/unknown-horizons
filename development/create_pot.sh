#!/bin/sh

# Create po/unknown-horizons.pot to be uploaded at pootle.
# (language Templates, project Unknown Horizons)
# Update strings extracted from xml, yaml and sql files.
# The flag -keep forces to skip this update.
# The flags -keepxml, keepyaml and -keepsql partially skip.
# Only use one of them.


VERSION=$(python2 -c 'from horizons.constants import VERSION
print "%s" % VERSION.RELEASE_VERSION')

RESULT_FILE=unknown-horizons.pot
XML_PY_FILE=horizons/i18n/guitranslations.py
YAML_PY_FILE=horizons/i18n/objecttranslations.py
SQL_POT_FILE=po/sqlite_strings.pot


if [ ! "x$1" = "x-keep" ]; then
	if [ ! "x$1" = "x-keepxml" ]; then
		python2 development/extract_strings_from_xml.py $XML_PY_FILE 2&>/dev/null
		echo "   * Regenerated xml translation file at $XML_PY_FILE."
	fi
	if [ ! "x$1" = "x-keepyaml" ]; then
		python2 development/extract_strings_from_objects.py $YAML_PY_FILE
		echo "   * Regenerated yaml translation file at $YAML_PY_FILE."
	fi
	if [ ! "x$1" = "x-keepsql" ]; then
		python2 development/extract_strings_from_sqlite.py > $SQL_POT_FILE
		echo "   * Regenerated sql translation file at $SQL_POT_FILE."
	fi
fi

# Get all files to translate.
(for python in *.py; do echo $python; done
    find editor   -name \*.py
    find horizons -name \*.py
    echo $SQL_POT_FILE
) | xgettext --files-from=- --output-dir=po --output=$RESULT_FILE \
             --from-code=UTF-8 --add-comments \
             --no-wrap --sort-by-file \
             --copyright-holder='The Unknown Horizons Team' \
             --package-name='Unknown Horizons' \
             --package-version="$VERSION" \
             --msgid-bugs-address='team@unknown-horizons.org' \
             --keyword=N_:1,2
#this also catches N_() plural-aware calls

# some strings contain two entries per line => remove line numbers from both
perl -pi -e 's,(#: .*):[0-9][0-9]*,\1,g' po/$RESULT_FILE
perl -pi -e 's,(#: .*):[0-9][0-9]*,\1,g' po/$RESULT_FILE

echo "=> Created gettext pot template file at po/$RESULT_FILE."
