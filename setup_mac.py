import os
# usage: 
# copy the full content/ folder into src/Contents/Resources/
# moreover copy the fife dir into the current dir
# details can be found at http://wiki.unknown-horizons.org/w/MacOS_build_notes

# Sets what directory to crawl for files to include
# Relative to location of setup.py; leave off trailing slash
includes_dir = 'src'

# Set the root directory for included files
# Relative to the bundle's Resources folder, so '../../' targets bundle root
includes_target = '../../'

# Initialize an empty list so we can use list.append()
data_includes = []

# Walk the includes directory and include all the files
for root, dirs, filenames in os.walk(includes_dir):
    if root is includes_dir:
        final = includes_target
    else:
        final = includes_target + root[len(includes_dir)+1:] + '/'
    files = []
    for file in filenames:
        if (file[0] != '.'):
            files.append(os.path.join(root, file))
    data_includes.append((final, files))


from setuptools import setup

packages = []
packages.append('horizons')
packages.append('fife')

#Info.plist keys for the app
#Icon.icns must be inside src/Contents/Resources/
plist = {"CFBundleIconFile": "Icon.icns",
		 "CFBundleDisplayName": "Unknown Horizons",
		 "CFBundleExecutable": "Unknown Horizons",
		 "CFBundleIdentifier": "org.unknown-horizons",
		 "CFBundleName": "Unknown Horizons",
		 "CFBundleShortVersionString": "0.0.0",
		 "LSArchitecturePriority": "i386",
		 "CFBundleVersion": "0.0.0"
		}

APP = ['run_uh.py']
OPTIONS = {'argv_emulation': True, 'packages': packages, 'plist':plist}

setup(
    app=APP,
    data_files=data_includes,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
