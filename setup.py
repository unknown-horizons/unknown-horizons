#!/usr/bin/env python2
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################


from __future__ import print_function
from distutils.core import setup
from distutils.command.build import build
from distutils.spawn import find_executable
import distutils.cmd
import os
import glob
import platform
from shutil import rmtree, copytree

from horizons.constants import VERSION

# Ensure we are in the correct directory
os.chdir(os.path.realpath(os.path.dirname(__file__)))

if platform.dist()[0].lower() in ('debian', 'ubuntu'):
	executable_path = 'games'
else:
	executable_path = 'bin'


# this trick is for setting RELEASE_VERSION if the code is cloned from git repository
if os.path.exists('.git'):
	with open('content/packages/gitversion.txt', 'w') as f:
		f.write(VERSION.RELEASE_VERSION)

data = [
  (executable_path, ('unknown-horizons', )),
  ('share/pixmaps', ('content/packages/unknown-horizons.xpm', )),
  ('share/unknown-horizons', ('content/settings-template.xml', )),
  ('share/man/man6', ('content/packages/unknown-horizons.6', )),
]

for root, dirs, files in filter(lambda x: len(x[2]), os.walk('content')):
	data.append(('share/unknown-horizons/{0!s}'.format(root),
		['{0!s}/{1!s}'.format(root, f) for f in files]))

packages = []
for root, dirs, files in os.walk('horizons'):
	packages.append(root)

# Add enet files for build platform
type = platform.system().lower()
arch = platform.machine()
dir = "horizons/network/{0!s}-x{1!s}".format(type, arch[-2:])
package_data = {dir: ['*.so']}


class _build_i18n(distutils.cmd.Command):
	"""
	Derived from https://launchpad.net/python-distutils-extra
	to avoid an additional dependency
	"""
	description = "integrate the gettext framework"
	user_options = [
		('desktop-files=', None, '.desktop.in files that should be merged'),
		('text-domains=', None, 'list of pairs of gettext domains & directory that holds the i18n files'),
		('bug-contact=', None, 'contact address for msgid bugs')
	]

	def initialize_options(self):
		self.desktop_files = []
		self.text_domains = []
		self.bug_contact = None

	def finalize_options(self):
		if not self.text_domains:
			self.text_domains = [(self.distribution.metadata.name, "po")]

	def generate_mo_files(self, domain, po_dir):
		if not os.path.isdir(po_dir):
			return []
		po_files = glob.glob("{}/*.po".format(po_dir))
		if po_files and not find_executable('msgfmt'):
			raise RuntimeError(
				"Can't generate language files, needs msgfmt. "
				"Only native language (English) will be available. "
				"Try installing the package 'gettext' or 'msgfmt'.")

		# If there is a po/LINGUAS file, or the LINGUAS environment variable
		# is set, only compile the languages listed there
		selected_languages = None
		linguas_file = os.path.join(po_dir, "LINGUAS")
		if os.path.isfile(linguas_file):
			with open(linguas_file) as f:
				selected_languages = f.read().split()
		if "LINGUAS" in os.environ:
			selected_languages = os.environ["LINGUAS"].split()

		mo_files = []
		for po_file in po_files:
			lang = os.path.basename(po_file[:-3])
			if selected_languages and lang not in selected_languages:
				continue
			mo_dir = os.path.join("content", "lang", lang, "LC_MESSAGES")
			mo_file = os.path.join(mo_dir, "{}.mo".format(domain))
			if not os.path.exists(mo_dir):
				os.makedirs(mo_dir)
			cmd = ["msgfmt", po_file, "-o", mo_file]
			po_mtime = os.path.getmtime(po_file)
			mo_mtime = os.path.exists(mo_file) and \
				os.path.getmtime(mo_file) or 0
			if po_mtime > mo_mtime:
				self.spawn(cmd)

			targetpath = os.path.join("share/locale", lang, "LC_MESSAGES")
			mo_files.append((targetpath, [mo_file]))
		return mo_files

	def run(self):
		"""
		Update the language files, generate mo files and add them
		to the to be installed files

		NOTE: This code is partly broken and hack-fixed to the state where it appears to work.
		It should be removed, since nobody understands the code well enough to be able to maintain it.

		"""
		text_domains = {}
		try:
			text_domains = eval(self.text_domains)
		except:
			pass

		if self.desktop_files and not find_executable('intltool-merge'):
			self.warn(
				"Can't generate desktop files, needs intltool-merge. "
				"Try installing the package 'intltool'.")
			return

		if self.bug_contact is not None:
			os.environ["XGETTEXT_ARGS"] = "--msgid-bugs-address={0}".format(self.bug_contact)
		data_files = self.distribution.data_files
		if data_files is None:
			# in case not data_files are defined in setup.py
			self.distribution.data_files = data_files = []

		mo_files_generated = False
		for (domain, po_dir) in text_domains:
			try:
				mo_files = self.generate_mo_files(domain, po_dir)
				if mo_files:
					mo_files_generated = True
				data_files.extend(mo_files)
			except RuntimeError as e:
				print(e.message)
				return

		# merge .in with translation
		for (option, switch) in ((self.desktop_files, "-d"),):
			try:
				file_set = eval(option)
			except:
				continue
			for (target, po_dir, files) in file_set:
				build_target = os.path.join("build", target)
				if not os.path.exists(build_target):
					os.makedirs(build_target)
				files_merged = []
				for file in files:
					if file.endswith(".in"):
						file_merged = os.path.basename(file[:-3])
					else:
						file_merged = os.path.basename(file)
					file_merged = os.path.join(build_target, file_merged)
					cmd = ["intltool-merge", switch, po_dir, file, file_merged]
					mtime_merged = os.path.exists(file_merged) and \
						os.path.getmtime(file_merged) or 0
					mtime_file = os.path.getmtime(file)
					if mo_files_generated or mtime_merged < mtime_file:
						# Only build if output is older than input (.po,.in)
						self.spawn(cmd)
					files_merged.append(file_merged)
				data_files.append((target, files_merged))

		# Since specifying a .mofile dir is not supported, we manually move build/mo/
		# to a place more appropriate in our opinion, currently content/lang/
		if os.path.exists(os.path.join("build", "mo")):
			# it appears build/mo should always magically appear,
			# but does not on some gentoo machines.
			# there, everything is placed in content/lang, so it's fine
			# on other machines, we have to move stuff around like that:
			if os.path.exists(os.path.join("content", "lang")):
				rmtree(os.path.join("content", "lang"))
			copytree(os.path.join("build", "mo"), os.path.join("content", "lang"))

build.sub_commands.append(('build_i18n', None))

cmdclass = {
    'build_i18n': _build_i18n,
}

setup(
    name='UnknownHorizons',
    version=VERSION.RELEASE_VERSION,
    description='Realtime Economy Simulation and Strategy Game',
    author='The Unknown Horizons Team',
    author_email='team@unknown-horizons.org',
    url='http://www.unknown-horizons.org',
    packages=packages,
    package_data=package_data,
    data_files=data,
    cmdclass=cmdclass)

# after installation remove gitversion.txt
if os.path.exists('.git'):
	os.unlink('content/packages/gitversion.txt')
