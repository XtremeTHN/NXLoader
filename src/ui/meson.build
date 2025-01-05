pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'nxloader' / 'ui'

ui_sources = [
    '__init__.py',
    'get_started_dialog.py',
    'not_found.py',
    'roms_page.py',
    'window.py'
]

install_data(ui_sources, install_dir: moduledir)