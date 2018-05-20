
import glob
import os

from horizons.constants import OLDPATHS, PATHS


def migrate_paths():

	migrated = False
	if check_cache_migration():
		migrate_cache()
		# cache migration doesn't really need a link or mention I think

	if check_config_migration():
		migrate_config()
		link_config()
		migrated = True

	if check_data_migration():
		migrate_data()
		link_data()
		migrated = True

	if migrated:
		leave_note()


def check_cache_migration():
	return os.path.isdir(OLDPATHS.CACHE_DIR) and not os.path.isdir(PATHS.CACHE_DIR)


def migrate_cache():
	cache_files = glob.glob(os.path.join(OLDPATHS.CACHE_DIR, "*.cache"))
	for oldname in cache_files:
		newname = os.path.join(PATHS.CACHE_DIR, os.path.basename(oldname))
		os.renames(oldname, newname)


def check_config_migration():
	return os.path.isfile(OLDPATHS.USER_CONFIG_FILE) and not os.path.isfile(PATHS.USER_CONFIG_FILE)


def migrate_config():
	os.renames(OLDPATHS.USER_CONFIG_FILE, PATHS.USER_CONFIG_FILE)


def link_config():
	os.symlink(PATHS.USER_CONFIG_FILE, OLDPATHS.USER_CONFIG_FILE)


def check_data_migration():
	return os.path.isdir(OLDPATHS.USER_DATA_DIR) and not os.path.isdir(PATHS.USER_DATA_DIR)


def migrate_data():
	os.renames(OLDPATHS.USER_DATA_DIR, PATHS.USER_DATA_DIR)


def link_data():
	os.symlink(PATHS.USER_DATA_DIR, OLDPATHS.USER_DATA_DIR)


def leave_note():
	notefile = os.path.join(PATHS.USER_DATA_DIR, "migration_readme.txt")
	notetext = """
In the latest version of unknown-horizons the user data directories have been moved.
This has been done automatically, and symlinks have been created to minimize inconvenience.

It is safe to remove these symlinks and this readme file.

If you ever downgrade the UH version you might need more care.

For more information, see the wiki:
https://github.com/unknown-horizons/unknown-horizons/wiki/2018-user-data-migration
"""
	print(notetext)
	with open(notefile, 'w') as f:
		f.write(notetext)
