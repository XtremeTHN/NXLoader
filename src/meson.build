pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'nxloader'
gnome = import('gnome')

blueprints = files(
	'ui/window.blp'
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

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
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
  'window.py',
]

install_data(nxloader_sources, install_dir: moduledir)
