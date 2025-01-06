pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'nxloader' / 'modules'

modules_sources = [
    '__init__.py',
    'switchfinder.py',
    'usbInstall.py',
    'glist.py'
]

install_data(modules_sources, install_dir: moduledir)