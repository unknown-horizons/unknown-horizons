# -.- coding: utf-8 -.-
# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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


"""This file includes conditions that are used in Unknown Horizons."""

def set_gold_amount(gold_amount):
	return {u'type': u'player_gold_greater', u'arguments': [gold_amount]}


def set_tier_limit(tier_limit):
	return {u'type': u'settler_level_greater', u'arguments': [tier_limit]}


def set_time_limit(time_limit):
	return {u'type': u'time_passed', u'arguments': [time_limit]}


def set_score_limit(score_limit):
		return {u'type': u'player_total_score_gt', u'arguments': [score_limit]}


def get_gold_limit(mp_conditions):
	return _("Gold Amount Limit: {limit}").format(limit=mp_conditions['gold_amount']['arguments'][0])


def get_score_limit(mp_conditions):
	return _("Score Limit: {limit}").format(limit=mp_conditions['score_limit']['arguments'][0])


def get_time_limit(mp_conditions):
	return _("Time Limit: {limit}").format(limit=mp_conditions['time_limit']['arguments'][0])


def get_tier_limit(mp_conditions):
	return _("Tier Limit: {limit}").format(limit=mp_conditions['tier_limit']['arguments'][0])


def conditions_to_yaml(mp_conditions):
	return {u'events': [{u'conditions': mp_conditions.values(), u'actions': [{u'type': u'logbook', u'arguments': [[u'Message', u'']]}]}]}