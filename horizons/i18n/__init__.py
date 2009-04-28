# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from guitranslations import set_translations
import horizons.main

set_translations()

all_translated_widgets = dict()

def set_text(widget, text):
    gui.find_child(name=widget).text = text

def set_title(widget, title):
    gui.findChild(name=widget).title = title

def load_xml_translated(filename):
    from guitranslations import text_translations
    #print text_translations
    global all_translated_widgets
    try:
        untranslated = horizons.main.fife.pychan.loadXML('content/gui/%s' % filename)
    except (IOError,ValueError), e:
        print e
        untranslated = horizons.main.fife.pychan.loadXML(filename)
    
    from os.path import basename
    filename = basename(filename)
    if text_translations.has_key(filename):
        for i in text_translations[filename].items():
            try:
                untranslated.findChild(name=i[0]).text = i[1]
            except AttributeError, e:
                print e
                print i, ' in ', filename
    elif horizons.main.debug:
        print _('No translation for file %s') % filename

    all_translated_widgets[filename] = untranslated

    return untranslated

def update_all_translations():
    set_translations()
    from guitranslations import text_translations
    global all_translated_widgets
    for pair in all_translated_widgets.items():
        for i in text_translations[pair[0]].items():
            try:
                pair[1].findChild(name=i[0]).text = i[1]
            except AttributeError, e:
                print e
                print i, ' in ', pair[0]
