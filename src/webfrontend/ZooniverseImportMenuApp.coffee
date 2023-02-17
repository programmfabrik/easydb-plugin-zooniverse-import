class ZooniverseImportMenuApp extends RootMenuApp

	@click: ->
		ez5.rootMenu.closeMenu()
		(new ZooniverseImport()).show()

	@is_allowed: ->
		ez5.session.hasSystemRight("root", "plugin.easydb-plugin-zooniverse-import.allow_use")

	@group: ->
		"za_importer"

	@label: ->
		"zooniverse_import.app.label"

	@isStartApp: ->
		false

	@submenu: ->
		"plugins"

ez5.session_ready ->
	ez5.rootMenu.registerApp(ZooniverseImportMenuApp)
