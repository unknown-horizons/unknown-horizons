#!/bin/sh

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** I changed or added a string in an xml file
# => Run  development/create_pot.sh
#
# ** I changed or added a string in an sql file
# => Run  development/create_pot.sh
#
# ** I changed or added a string in an object yaml file
# => Run  development/create_pot.sh
#
# ** I changed a string in a py file
# => Do nothing, everything is fine
#
# ** I added a string 'New string' to a py file and it should be translated
# => Use _('New string') instead of 'New string'.
#
# ** The string uses a formatting placeholder like 'num: {amount}' or 'num: %s'
# => Only *ever* use the named  _('num: {amount}')  syntax. Translators have no
#    idea what '%s' means, especially with multiple substitutions. BIG FAT NOTE
#    You will need to add the following line right before your string in python
#      #xgettext:python-format
#    for the string to be properly recognized in pootle.          /BIG FAT NOTE
#    This comment can also go inline after the format string, but prefer above.
#
# ** I changed or added strings in the tutorial yaml file
# => Run  development/create_scenario_pot.sh tutorial
#
# ** I changed or added strings in the yaml file of a translated scenario named
#    "foobar_en.yaml"
# => Run  development/create_scenario_pot.sh foobar
#
# ** I want to see the current translations from pootle in-game
# => Run  development/copy_pofiles.sh && ./setup.py build_i18n
#
# ** I have no idea what 'i18n' means
# => Short for 'internationalization': i + 18 letters + n.
#    Also see  http://en.wikipedia.org/wiki/i18n  for more info.
#
###############################################################################
#
# Create pot files to be uploaded at pootle.
# (language Templates, project Unknown Horizons)
# Update strings extracted from xml, yaml and sql files.
# The flag -keep forces to skip this update.
# The flags -keepxml, keepyaml and -keepsql partially skip.
# Only use one of them.

# script assumes working dir to be our base directory
cd "$(dirname "$0")"/..

VERSION=$(python2 -c 'from horizons.constants import VERSION
print "%s" % VERSION.RELEASE_VERSION')

RESULT_FILE=po/uh/unknown-horizons.pot
RESULT_FILE_SERVER=po/uh-server/unknown-horizons-server.pot
XML_PY_FILE=horizons/i18n/guitranslations.py
YAML_PY_FILE=horizons/i18n/objecttranslations.py
SQL_POT_FILE=horizons/i18n/sqlite_strings.pot

function strip_entries()
{
  # some strings contain two entries per line => remove line numbers from both
  perl -pi -e 's,(#: .*):[0-9][0-9]*,\1,g' $1
  perl -pi -e 's,(#: .*):[0-9][0-9]*,\1,g' $1
}

if [ ! "x$1" = "x-keep" ]; then
	if [ ! "x$1" = "x-keepxml" ]; then
		PYTHONPATH="." python2 development/extract_strings_from_xml.py $XML_PY_FILE 2&>/dev/null
		echo "   * Regenerated xml translation file at $XML_PY_FILE."
	fi
	if [ ! "x$1" = "x-keepyaml" ]; then
		PYTHONPATH="." python2 development/extract_strings_from_objects.py $YAML_PY_FILE
		echo "   * Regenerated yaml translation file at $YAML_PY_FILE."
	fi
	if [ ! "x$1" = "x-keepsql" ]; then
		PYTHONPATH="." python2 development/extract_strings_from_sqlite.py > $SQL_POT_FILE
		echo "   * Regenerated sql translation file at $SQL_POT_FILE."
	fi
fi

# Get all files to translate.
(
  find . -mindepth 1 -maxdepth 1 -name \*.py && \
  find horizons -name \*.py && \
  echo $SQL_POT_FILE
) | xgettext --files-from=- --output=$RESULT_FILE \
             --from-code=UTF-8 --add-comments \
             --no-wrap --sort-by-file \
             --copyright-holder='The Unknown Horizons Team' \
             --package-name='Unknown Horizons' \
             --package-version="$VERSION" \
             --msgid-bugs-address='team@unknown-horizons.org' \
             --keyword=N_:1,2
#this also catches N_() plural-aware calls
strip_entries $RESULT_FILE
echo "=> Created UH gettext pot template file at ${RESULT_FILE}."


# generate translation file for server
# --keyword disables all known keywords
(
  find horizons/network -iname \*.py
) | xgettext --files-from=- --output=$RESULT_FILE_SERVER \
             --from-code=UTF-8 --add-comments \
             --no-wrap --sort-by-file \
             --copyright-holder='The Unknown Horizons Team' \
             --package-name='Unknown Horizons Server' \
             --package-version="$VERSION" \
             --msgid-bugs-address='team@unknown-horizons.org' \
             --keyword \
             --keyword=S_:2 \
             --keyword=SN_:2,3 \
             --keyword=__
strip_entries $RESULT_FILE_SERVER
echo "=> Created UH Server gettext pot template file at ${RESULT_FILE_SERVER}."
