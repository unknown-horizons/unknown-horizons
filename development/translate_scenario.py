#!/usr/bin/env python2
# Encoding: utf-8
# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import gettext
import os
import re
import subprocess
import sys
import yaml

# Where to find initial untranslated scenario (with language `en`) and,
# simultaneously, where to write final translated scenario .yaml to
YAML_PATH = '{path_prefix}content/scenarios/{scenario}_{language}.yaml'
# Where to write compiled (bytecode) translations for scenarios to.
# Note: this is a temporary path and only required as intermediate step.
MO_OUTPUT = 'po/mo/'
MSGFMT_PATH = '{MO_OUTPUT}/{language}/LC_MESSAGES/'
# Where we store our gettext scenario translation files (in non-GNU layout)
PO_INPUT_PATH = 'po/scenarios/{language}/{scenario}.po'

# po/scenarios/sv/The_Unknown.po
WEBLATE_PATH = re.compile(r'''
    (.*/?)         # path to UH in Weblate repo
    po/scenarios/  # path in UH repo
    ([^/]*)/       # \2 == 'sv'
    ([^\.]*)\.po   # \3 == 'The_Unknown'
    ''', re.VERBOSE)


def setup_paths():
    match = WEBLATE_PATH.match(sys.argv[1])
    path_prefix = match.group(1)
    # ISO 639-1 code of desired translation on Weblate (`af`, `hr`, ...)
    language_path = match.group(2)
    # name of English .yaml scenario file
    scenario_path = match.group(3)

    if not os.path.exists(scenario_path):
        scenario_path = YAML_PATH.format(path_prefix=path_prefix,
                                         scenario=scenario_path,
                                         language='en')
    if not os.path.exists(scenario_path):
        print 'Scenario file not found:', scenario_path
        sys.exit(1)

    # drop [_en].yaml suffix and paths to file to obtain base scenario name
    scenario = os.path.splitext(os.path.basename(scenario_path))[0]
    if scenario.endswith('_en'):
        scenario = scenario[:-3]

    if os.path.exists(language_path):
        dirname = os.path.dirname(language_path)
        language = dirname.split(os.path.sep)[-1]
    else:
        language = language_path
        language_path = PO_INPUT_PATH.format(scenario=scenario,
                                             language=language)

    yaml_output = YAML_PATH.format(path_prefix=path_prefix, scenario=scenario,
                                   language=language)
    msgfmt_output = MSGFMT_PATH.format(MO_OUTPUT=MO_OUTPUT,
                                       language=language) +\
        '{0!s}.mo'.format(scenario)

    # If path for compiled translations does not exist yet, create it
    subprocess.call(['mkdir', '-p', MSGFMT_PATH.format(MO_OUTPUT=MO_OUTPUT,
                                                       language=language)])

    return (path_prefix,
            scenario, scenario_path,
            language, language_path,
            yaml_output, msgfmt_output)


def setup_gettext(scenario, language):
    try:
        translation = gettext.translation(scenario, MO_OUTPUT, [language])
    except IOError:
        # IOError: [Errno 2] No translation file found for domain
        print('No compiled translation for domain `%s` and '
              'language `%s` in `%s`. Exiting.' % (scenario, language,
                                                   MO_OUTPUT))
        sys.exit(1)
    else:
        translation.install(unicode=True)


def compile_scenario_po(output_mo):
    input_po = sys.argv[1]
    if not os.path.exists(input_po):
        print('Input file does not exist: {0!s}'.format(input_po))
        sys.exit(1)
    try:
        stats = subprocess.check_output([
            'msgfmt',
            '--statistics',
            '--check-format',
            input_po,
            '-o', output_mo,
        ], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        # TODO handle
        print('Error while compiling translation `%s`, probably malformed '
              '`.po`. Exiting.' % input_po)
        sys.exit(1)
    else:
        return stats


def write_translated_yaml(fileish, where, metadata, generator):
    """Copy content of .yaml scenario file while translating parts of it.

    In particular, arguments of these event types will be translated:
        Headline, Label, Message
    Uses a regular gettext .po file on Weblate to read translations from.
    The .pot template file for those currently is generated by invoking
    `create_scenario_pot.sh` with the scenario name as parameter.
    Scenario translation files are stored in po/scenarios/.
    """

    def translate(string):
        return _(string.rstrip('\n'))

    def preprint(yamlish, new_anchor, just_copy=True):
        """Prepare untranslated .yaml input *yamlish* for translation

        Depending on current state of our manual parser, we either want to
        just copy the lines (because there is nothing to translate), or pass
        some arguments to gettext where they will be translated and written
        back to the new file.
        To retain yaml anchors (`&THESE_THINGS`) and their references, split
        the yaml stream into chunks for each anchor we detect. Using
        yaml.SafeLoader on those chunks is possible to obtain correct data
        structures (since we are hacking the output to repair indentation).
        """
        if just_copy:
            where.writelines(yamlish)
            where.write(new_anchor)
            return

        new_anchor = new_anchor.rstrip('\n')
        loaded_yaml = yaml.safe_load(''.join(yamlish))
        all_events = []
        for event in loaded_yaml:
            if isinstance(event, basestring):
                if event.strip():
                    event = translate(event)
            if isinstance(event, list):
                widget = event[0]
                if widget in ('Gallery', 'Image', 'Pagebreak'):
                    pass
                if widget in ('Headline', 'Label', 'BoldLabel', 'Message'):
                    event = [widget] + map(translate, event[1:])

            all_events.append(event)

        # allow_unicode: Without this, would dump '\xF6' instead of 'ö'.
        # width: Default width would wrap at ~80 chars,
        #  not matching the english sources
        dumpster = yaml.safe_dump(all_events, allow_unicode=True, width=1000)
        # Manually indent since we manually keep anchors
        # (pyyaml would rename and otherwise mess with them)
        for line in dumpster.split('\n'):
            indent = '  ' if line else ''
            where.write(indent + line + '\n')

        where.write(new_anchor + '\n')

    def write_translated_metadata(translated_metadata):
        # Prepare 'metadata' dictionary for the translated scenario
        file_metadata = yaml.safe_load(''.join(fileish))['metadata']
        translated_metadata = file_metadata.copy()
        # Manually invoke translation of strings exposed to player that are
        # reasonable to translate.
        for key in ('author', 'description', 'difficulty'):
            value = file_metadata[key]
            translated_metadata[key] = translate(value)
        # Add (untranslated) information passed to this function, such as
        # translation status from gettext or the file locale, if available.
        if metadata:
            translated_metadata.update(metadata)
        # All of this is dumped to file when we encounter a 'metadata:' line
        # while manually parsing the original scenario line-by-line. Ugly.
        m = {'metadata': translated_metadata}
        dumped = yaml.safe_dump(m, allow_unicode=True, width=1000,
                                default_flow_style=False)
        where.write(dumped)

    where.write('''\
# DO NOT MANUALLY EDIT THIS FILE.

# It was automatically generated by {0}
# using translation files from Weblate and the original scenario file
# {1}
\n'''.format(generator, metadata['original']))

    # Manually track currently seen anchor (to delimit sections)
    anchors = []
    # List of yaml content lines for each section (to be loaded by `yaml`)
    sections = [[]]
    # Copy everything looking like a header (lines before the first anchor)
    seen_start_anchor = False
    # Copy everything after `logbook-data`
    #  (scenario conditions/actions, metadata)
    copy_again = False

    for line in fileish:

        if copy_again:
            if line.startswith('metadata:'):
                write_translated_metadata(1)
                break
            where.write(line)

        elif line.startswith('- '):
            # New anchor detected.
            # If this is our first anchor, stop just copying lines
            # and enter translation mode instead (seen_start_anchor)
            anchors.append(line)
            preprint(sections[-1], anchors[-1],
                     just_copy=not seen_start_anchor)
            sections.append([])

            if not seen_start_anchor:
                seen_start_anchor = True

        elif line.startswith('events:'):
            # Only try to translate logbook-data.
            #  This ends logbook-data section.
            anchors.append(line)
            preprint(sections[-1], anchors[-1],
                     just_copy=not seen_start_anchor)
            sections.append([])

            # Thus, abort and only copy from here on
            copy_again = True

        else:
            sections[-1].append(line)


def main():
    (path_prefix, scenario, scenario_path, language, language_path,
     yaml_output, msgfmt_output) = setup_paths()
    # This writes .mo files in the *scenario* domain, so setup_gettext needs
    # to come afterwards!
    tl_status = compile_scenario_po(msgfmt_output)
    setup_gettext(scenario, language)

    metadata = {
        'translation_status': tl_status.rstrip(),
        'locale': language,
        'original': scenario_path[len(path_prefix):],
    }

    generator = os.path.join('development', os.path.basename(__file__))

    with open(yaml_output, 'w') as out:
        with open(scenario_path, 'r') as f:
            english_scenario = f.readlines()
        write_translated_yaml(english_scenario, out, metadata, generator)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {0} scenario_translation_file'
              .format(os.path.basename(__file__)))
        print('\tscenario_translation_file: `po/scenarios/sv/tutorial.po`')
        print('Run from main UH directory!')
        sys.exit(1)
    else:
        main()
