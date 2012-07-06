#!/usr/bin/env python

from __future__ import with_statement
from distutils.core import setup
from distutils.command.build import build
from distutils.spawn import spawn, find_executable
import distutils.cmd
import os
import glob
import platform
from shutil import rmtree, copytree

# Install dummy gettext before any imports from horizons
import gettext
gettext.install("")

from horizons.constants import VERSION

# Ensure we are in the correct directory
os.chdir(os.path.realpath(os.path.dirname(__file__)))

if platform.dist()[0].lower() in ('debian', 'ubuntu'):
	executable_path = 'games'
else:
	executable_path = 'bin'


#this trick is for setting RELEASE_VERSION if the code is cloned from git repository
if os.path.exists('.git'):
	f = open('content/gitversion.txt', 'w')
	f.write(VERSION.RELEASE_VERSION)
	f.close()

data = [
  (executable_path, ('unknown-horizons', )),
  ('share/pixmaps', ('content/unknown-horizons.xpm', )),
  ('share/unknown-horizons', ('content/settings-template.xml', ))
]

for root, dirs, files in filter(lambda x: len(x[2]), os.walk('content')):
	data.append(('share/unknown-horizons/%s' % root,
				       ['%s/%s' % (root, f) for f in files]))

packages = []
for root, dirs, files in os.walk('horizons'):
	packages.append(root)

# Add enet files for build platform
type = platform.system().lower()
arch = platform.machine()
dir = "horizons/network/%s-x%s" % (type, arch[-2:])
package_data = { dir: ['*.so'] }

class _build_i18n(distutils.cmd.Command):
	"""
	Derived from https://launchpad.net/python-distutils-extra
	to avoid an additional dependency
	"""
	description = "integrate the gettext framework"
	user_options = [('desktop-files=', None, '.desktop.in files that should be merged'),
				          ('domain=', 'd', 'gettext domain'),
				          ('po-dir=', 'p', 'directory that holds the i18n files'),
				          ('bug-contact=', None, 'contact address for msgid bugs')]

	def initialize_options(self):
		self.desktop_files = []
		self.domain = None
		self.bug_contact = None
		self.po_dir = None

	def finalize_options(self):
		if self.domain is None:
			self.domain = self.distribution.metadata.name
		if self.po_dir is None:
			self.po_dir = "po"

	def run(self):
		"""
		Update the language files, generate mo files and add them
		to the to be installed files

		NOTE: This code is partly broken and hack-fixed to the state where it appears to work.
		      It should be removed, since nobody understands the code well enough to be able to maintain it.

		"""
		if not os.path.isdir(self.po_dir):
			return
		po_files = glob.glob("%s/*.po" % self.po_dir)
		if po_files and not find_executable('msgfmt'):
			self.warn("Can't generate language files, needs msgfmt. "
				"Only native language (English) will be available. "
				"Try installing the package 'gettext' or 'msgfmt'.")
			return
		if self.desktop_files and not find_executable('intltool-merge'):
			self.warn("Can't generate desktop files, needs intltool-merge. "
				"Try installing the package 'intltool'.")
			return

		data_files = self.distribution.data_files
		if data_files is None:
			# in case not data_files are defined in setup.py
			self.distribution.data_files = data_files = []

		if self.bug_contact is not None:
			os.environ["XGETTEXT_ARGS"] = "--msgid-bugs-address=%s " % self.bug_contact

		# If there is a po/LINGUAS file, or the LINGUAS environment variable
		# is set, only compile the languages listed there.
		selected_languages = None
		linguas_file = os.path.join(self.po_dir, "LINGUAS")
		if os.path.isfile(linguas_file):
			selected_languages = open(linguas_file).read().split()
		if "LINGUAS" in os.environ:
			selected_languages = os.environ["LINGUAS"].split()

		max_po_mtime = 0
		for po_file in po_files:
			lang = os.path.basename(po_file[:-3])
			if selected_languages and not lang in selected_languages:
				continue
			mo_dir = os.path.join("content", "lang", lang, "LC_MESSAGES")
			mo_file = os.path.join(mo_dir, "%s.mo" % self.domain)
			if not os.path.exists(mo_dir):
				os.makedirs(mo_dir)
			cmd = ["msgfmt", po_file, "-o", mo_file]
			po_mtime = os.path.getmtime(po_file)
			mo_mtime = os.path.exists(mo_file) and \
				os.path.getmtime(mo_file) or 0
			if po_mtime > max_po_mtime:
				max_po_mtime = po_mtime
			if po_mtime > mo_mtime:
				self.spawn(cmd)

			targetpath = os.path.join("share/locale", lang, "LC_MESSAGES")
			data_files.append((targetpath, (mo_file,)))

		# merge .in with translation
		for (option, switch) in ((self.desktop_files, "-d"),):
			try:
				file_set = eval(option)
			except:
				continue
			for (target, files) in file_set:
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
					cmd = ["intltool-merge", switch, self.po_dir, file, file_merged]
					mtime_merged = os.path.exists(file_merged) and \
						os.path.getmtime(file_merged) or 0
					mtime_file = os.path.getmtime(file)
					if mtime_merged < max_po_mtime or mtime_merged < mtime_file:
							# Only build if output is older than input (.po,.in)
						self.spawn(cmd)
					files_merged.append(file_merged)
				data_files.append((target, files_merged))

		# Since specifying a .mofile dir is not supported, we manually move build/mo/
		# to a place more appropriate in our opinion, currently content/lang/.

		if os.path.exists(os.path.join("build", "mo")):
			# it appears build/mo should always magically appear, but does not on some gentoo machines.
			# there, everything is placed in content/lang, so it's fine
			# on other machines, we have to move stuff around like that:
			if os.path.exists(os.path.join("content", "lang")):
				rmtree(os.path.join("content", "lang"))
			copytree(os.path.join("build", "mo"), \
							 os.path.join("content", "lang"))

build.sub_commands.append(('build_i18n', None))

class _build_man(build):
	description = "build the Manpage"

	def run(self):
		if not find_executable('xsltproc'):
			self.warn("Can't build manpage, needs xsltproc")
			return

		self.make_file(['doc/manpage.xml'], 'unknown-horizons.6', spawn, \
								   (['xsltproc',
								     'http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl',
								     'doc/manpage.xml'],))
		self.distribution.data_files.append(('share/man/man6', ('unknown-horizons.6',)))

build.sub_commands.append(('build_man', None))

cmdclass = {
  'build_man': _build_man,
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

#after installation remove gitversion.txt
if os.path.exists('.git'):
	os.unlink('content/gitversion.txt')
