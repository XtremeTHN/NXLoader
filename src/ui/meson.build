pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'nxloader' / 'ui'

ui_sources = [
    '__init__.py',
    'dialogs.py',
    'not_found.py',
    'roms_page.py',
    'exception_dialog.py',
    'window.py'
]

install_data(ui_sources, install_dir: moduledir)

subdir('blueprints')