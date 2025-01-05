pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'nxloader'
gnome = import('gnome')

blueprints = files(
	'ui/blueprints/window.blp',
  'ui/blueprints/dialog.blp',
  'ui/blueprints/not_found_page.blp',
  'ui/blueprints/rom.blp',
  'ui/blueprints/roms_page.blp',
)

gnome.compile_resources('nxloader',
  'nxloader.gresource.xml',
  gresource_bundle: true,
  dependencies: custom_target('blueprints',
    input: blueprints,
    output: '.',
    command: [
      find_program('blueprint-compiler'),
      'batch-compile',
      '@OUTPUT@',
      '@CURRENT_SOURCE_DIR@',
      '@INPUT@'
    ]),
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')
python_i = python.find_installation('python3', modules: ['usb', 'gi'])

conf = configuration_data()
conf.set('PYTHON', python_i.full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'nxloader.in',
  output: 'nxloader',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

nxloader_sources = [
  '__init__.py',
  'main.py',
]

install_data(nxloader_sources, install_dir: moduledir)

subdir('modules')
subdir('ui')