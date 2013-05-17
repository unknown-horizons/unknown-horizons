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
#    for the string to be properly recognized in Weblate.         /BIG FAT NOTE
#    This comment can also go inline after the format string, but prefer above.
#
# ** I changed or added strings in the tutorial yaml file
# => Run  development/create_scenario_pot.sh tutorial
#
# ** I changed or added strings in the yaml file of a translated scenario named
#    "foobar_en.yaml"
# => Run  development/create_scenario_pot.sh foobar
#
# ** I want to see the current translations from Weblate in-game
# => Run  ./setup.py build_i18n
# => You can instead follow this guide:
#    http://github.com/unknown-horizons/unknown-horizons/wiki/Interface-translation
#
# ** I have no idea what 'i18n' means
# => Short for 'internationalization': i + 18 letters + n.
#    Also see  http://en.wikipedia.org/wiki/i18n  for more info.
#
###############################################################################
#
# Create pot files for the Weblate subprojects "Interface" (`uh/uh/`) and
# "MP-Server" (`uh/uh-server/`).
# Update strings extracted from xml, yaml and sql files.
#
# You may want to run  development/update_translations.py  afterwards to
# update all translation files against those new templates.

set -e

# script assumes working dir to be our base directory
cd "$(dirname "$0")"/..

VERSION=$(python2 -c 'from horizons.constants import VERSION
print "%s" % VERSION.RELEASE_VERSION')

RESULT_FILE=po/uh/unknown-horizons.pot
RESULT_FILE_SERVER=po/uh-server/unknown-horizons-server.pot
XML_PY_FILE=horizons/i18n/guitranslations.py
YAML_PY_FILE=horizons/i18n/objecttranslations.py
SQL_POT_FILE=po/sqltranslations.pot

function strip_itstool()
{
  # Remove lines containing comments like these ones:
  #. (itstool) path: Container/Label@text
  #. (itstool) comment: Container/Label@text
  sed -i '/^#\. (itstool) /d' $1
  sed -i '/^#\. noi18n_\(help\)\?text$/d' $1
}

function reset_if_empty()
{
  # See whether anything except version and date changed in header (2+ 2-)
  # If so, reset file to previous version in git (no update necessary)
  numstat=$(git diff --numstat -- "$1" | cut -f1,2)
  if [ "$numstat" = "2	2" ]; then
    echo "  -> No content changes in $1, resetting to previous state."
    git checkout -- "$1"
  fi
}

# XML files
PYTHONPATH="." python2 development/extract_strings_from_xml.py "$XML_PY_FILE"
echo "   * Regenerated xml translation file at $XML_PY_FILE."
find content/gui/xml/{editor,ingame,mainmenu} -name "*.xml" | xargs \
  itstool -i development/its-rule-pychan.xml \
          -i development/its-rule-uh.xml \
          -o "$RESULT_FILE"
echo "   * Wrote xml translation template to $RESULT_FILE."

# YAML files
PYTHONPATH="." python2 development/extract_strings_from_objects.py "$YAML_PY_FILE"
echo "   * Regenerated yaml translation file at $YAML_PY_FILE."

echo "=> Creating UH gettext pot template file at $RESULT_FILE."

# Python files
(
  find . -mindepth 1 -maxdepth 1 -name \*.py && \
  find horizons \( -name \*.py ! -name "guitranslations.py" \) \
) | xgettext --files-from=- --output="$RESULT_FILE" \
             --join-existing \
             --from-code=UTF-8 --add-comments \
             --no-wrap --sort-by-file \
             --copyright-holder='The Unknown Horizons Team' \
             --package-name='Unknown Horizons' \
             --package-version="$VERSION" \
             --msgid-bugs-address='team@unknown-horizons.org' \
             --keyword=N_:1,2 \
             --keyword=_lazy
# --keyword=N_ also catches N_() plural-aware ngettext calls

# SQL files
PYTHONPATH="." python2 development/extract_strings_from_sqlite.py > "$SQL_POT_FILE"
echo "   * Regenerated sql translation file at $SQL_POT_FILE."
# Merge with python+xml file RESULT_FILE, do not update header
xgettext --output="$RESULT_FILE" \
         --join-existing \
         --omit-header \
         "$SQL_POT_FILE"

# Some make-up
strip_itstool "$RESULT_FILE"
reset_if_empty "$RESULT_FILE"


# generate translation file for server
# empty --keyword disables all known keywords
echo "=> Creating UH Server gettext pot template file at $RESULT_FILE_SERVER."
(
  find horizons/network -iname \*.py
) | xgettext --files-from=- --output="$RESULT_FILE_SERVER" \
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
reset_if_empty "$RESULT_FILE_SERVER"
