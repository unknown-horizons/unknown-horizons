# -*- coding: utf-8 -*-

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

import unittest
import pep8


class TestCodeFormat(unittest.TestCase):

    def test_pep8_conformance(self):
        """Test that code conform to PEP8."""
        pep8style = pep8.StyleGuide(quiet=False)
        result = pep8style.check_files(
            ['run_tests.py',
             'run_server.py',
             'run_uh.py',
             'setup.py',
             'setup_mac.py',
             'stage_build_mac.py',
             ])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_pep8_dir_tests(self):
        """Test that code conform to PEP8."""
        pep8style = pep8.StyleGuide(quiet=False)
        result = pep8style.check_files(
            ['tests/__init__.py',
             'tests/utils.py',
             'tests/unittests/__init__.py',
             'tests/unittests/test_messages.py',
             'tests/unittests/test_network.py',
             'tests/unittests/test_pep8.py',
             'tests/unittests/test_scheduler.py',
             'tests/unittests/test_timer.py',
             'tests/unittests/gui/__init__.py',
             'tests/unittests/gui/test_window_manager.py',
             'tests/unittests/misc/test_paths.py',
             'tests/unittests/util/__init__.py',
             'tests/unittests/util/test_color.py',
             'tests/unittests/util/test_registry.py',
             'tests/unittests/util/test_shapes.py',
             'tests/unittests/world/__init__.py',
             'tests/unittests/world/buildability/__init__.py',
             'tests/unittests/world/component/__init__.py',
             'tests/unittests/world/production/__init__.py',
             'tests/unittests/world/production/test_productionline.py',
             'tests/unittests/world/units/__init__.py',
             'tests/unittests/world/units/collectors/__init__.py',
             'tests/unittests/world/units/collectors/test_collector.py',
             'tests/gui/__init__.py',
             'tests/gui/cooperative.py',
             ])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")


if __name__ == '__main__':
    unittest.main()
