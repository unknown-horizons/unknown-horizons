# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
# ###################################################

from typing import Optional
from unittest import mock

import pytest

from tests.gui.helper import GuiHelper


class Widget:
    """
    Fake widget with a name, children and possible a parent. All children of
    this widget will get their parent attribute set to this widget.
    """

    def __init__(self, name, children=None):
        self.name = name
        self.parent = None  # type: Optional["Widget"]
        self.children = children or []

        for child in self.children:
            child.parent = self

    def __repr__(self):
        return self.name

    def __hash__(self):
        return id(self)


@pytest.fixture
def widgets():
    return set()


@pytest.fixture
def widget_factory(widgets):
    def create(name, children=None):
        widget = Widget(name, children)
        widgets.add(widget)
        return widget

    return create


@pytest.fixture
def find(widgets):
    helper = GuiHelper(mock.Mock(), mock.Mock())
    return lambda path: helper._find(widgets, path)


def test_simple(widget_factory, find):
    """Single widget in the global list."""
    target = widget_factory("target")

    assert find("target") == target


def test_parent(widget_factory, find):
    """Single widget with a child."""
    target = widget_factory("target")

    widget_factory(
        "foobar",
        [
            target,
        ],
    )

    assert find("target") == target


def test_hierarchy(widget_factory, find):
    """
    Target widget with multiple parents and another widget with the same name,
    but without parent.
    """
    target = widget_factory("target")

    widget_factory(
        "bla",
        [
            widget_factory(
                "baz",
                [
                    target,
                ],
            )
        ],
    )

    widget_factory("foobar")
    widget_factory("target")

    assert find("bla/baz/target") == target


def test_hierarchy_incomplete_path(widget_factory, find):
    """
    Target with multiple parents, select it while omitting one parent in the
    search path.
    """
    target = widget_factory("target")

    widget_factory(
        "bla",
        [
            widget_factory(
                "baz",
                [
                    target,
                ],
            )
        ],
    )

    widget_factory("foobar")
    widget_factory("target")

    assert find("bla/target") == target


def test_hierarchy_returns_widget_with_best_matching_path(
    widget_factory,
    find,
):
    """
    If we have multiple matches for a path, return the one that fits most
    closely, i.e. the one with the shortest path of names.
    """
    target1 = widget_factory("target")
    target2 = widget_factory("target")

    widget_factory(
        "bla",
        [
            widget_factory(
                "baz",
                [
                    target1,
                ],
            )
        ],
    )

    widget_factory(
        "bla",
        [
            target2,
        ],
    )

    assert find("bla/target") == target2


def test_ambigious_error(widget_factory, find):
    """
    If a single best match can't be found, an error is raised instead.
    """
    target1 = widget_factory("target")
    target2 = widget_factory("target")

    widget_factory(
        "bla",
        [
            target1,
        ],
    )

    widget_factory(
        "bla",
        [
            target2,
        ],
    )

    with pytest.raises(Exception, match=r"Ambigious specification bla/target, found 2 matches"):
        find("bla/target")


def test_hierarchy_not_absolute_path(widget_factory, find):
    """
    Target with multiple parents, select it without specifing the top-most
    widget.
    """
    target = widget_factory("target")

    widget_factory(
        "bla",
        [
            widget_factory(
                "baz",
                [
                    target,
                ],
            )
        ],
    )

    widget_factory("foobar")
    widget_factory("target")

    assert find("baz/target") == target


def test_wrong_search_path(widget_factory, find):
    """
    A previous implementation had a bug where the code would go in a dead end
    when one part of the path matches, but children below won't.
    """
    target = widget_factory("target")

    widget_factory(
        "wrongpath",
        [
            widget_factory("foobar"),
        ],
    )

    widget_factory(
        "foobar",
        [
            target,
        ],
    )

    assert find("foobar/target") == target


def test_multiple_siblings(widget_factory, find):
    """
    Target widget with multiple parents and multiple siblings.
    """
    target = widget_factory("target")

    widget_factory(
        "bla",
        [
            widget_factory(
                "baz",
                [
                    widget_factory("sibling1"),
                    target,
                    widget_factory("sibling2"),
                    widget_factory("sibling3"),
                ],
            )
        ],
    )

    assert find("bla/baz/target") == target


def test_target_with_childrens(widget_factory, find):
    """
    Make sure that the target is still found even if it has children itself.
    """
    target = widget_factory(
        "target",
        [
            widget_factory("baz"),
            widget_factory(
                "foo",
                [
                    widget_factory("bar"),
                ],
            ),
        ],
    )

    widget_factory(
        "bla",
        [
            widget_factory(
                "baz",
                [
                    target,
                ],
            )
        ],
    )

    assert find("bla/baz/target") == target
