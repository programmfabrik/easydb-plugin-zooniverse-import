class ZooniverseImport extends CUI.Element

	constructor: (@opts={}) ->
		super(@opts)
		@__init()

	initOpts: ->
		super()

	show: ->
		@__modal.show()
		return

	__parse_fields: (masks, path) ->
		for mask in masks

			if not "fields" of mask
				continue

			for field in mask.fields
				if not "kind" of field
					continue

				if field.kind == "field"

					if not "column_id" of field
						continue

					if not "_column" of field
						continue
					if not "name" of field._column
						continue
					if not "type" of field._column
						continue

					if field._column.type not in ["string", "text", "text_oneline", "text_l10n", "text_l10n_oneline", "date", "datetime"]
						continue

					@__columns_by_id[String(field.column_id)] =
						name: field._column.name
						type: field._column.type
					if path.length > 0
						@__columns_by_id[String(field.column_id)]["path"] = path

					continue

				if field.kind == "link"

					if not "_column" of field
						continue
					if not "name" of field._column
						continue

					if not "_other_table" of field
						continue
					if not "_preferred_mask" of field._other_table
						continue
					if not "name" of field._other_table
						continue

					new_path = []
					for p in path
						new_path.push p
					new_path.push
						type: "link"
						name: field._column.name
						objecttype: field._other_table.name

					@__parse_fields([field._other_table._preferred_mask], new_path)

					continue

				if field.kind == "linked-table"

					if not "mask" of field
						continue

					if not "_other_table" of field
						continue
					if not "name" of field._other_table
						continue

					new_path = []
					for p in path
						new_path.push p
					new_path.push
						type: "_nested"
						name: field._other_table.name

					@__parse_fields([field.mask], new_path)

					continue

	__log_events: ->
		for e in @__events
			if not "type" of e
				continue
			if not e.type in ["ZOONIVERSE_IMPORT_INSERT", "ZOONIVERSE_IMPORT_UPDATE"]
				continue

			event =
				type: e.type
				pollable: false
			if "info_json" of e
				event.info = e.info_json

			EventPoller.saveEvent(event)


	__init: ->
		# plugin needs information about the datamodel
		# api callback can not load all necessary information about the datamodel
		# for each table, get the name by id and the corresponding mask

		@__columns_by_id = {}
		@__parse_fields(ez5.mask.CURRENT.masks, [])

		@__parseButton = new CUI.Button
			text: $$("zooniverse.importer.modal_content.parse_csv_button.label")
			disabled: true
			onClick: =>
				@__parseCSV()

		@__modalContent = new CUI.VerticalList
			class: "ez5-zooniverse-importer-list"
			content: [
				new CUI.Label
					text: $$("zooniverse.importer.modal_content.header.label")
			,
				new CUI.FileUploadButton
					fileUpload: @__getUploadFileReader()
					text: $$("zooniverse.importer.modal_content.upload_csv_button.label")
					multiple: false
					onClick: =>
						@__importButton.disable()
			,
				@__parseButton
			]

		@__importButton = new CUI.Button
			text: $$("zooniverse.importer.import_button.label")
			primary: true
			disabled: true
			onClick: => # xxx

				# todo import generated objects (like in JSON importer):
				#
				# objects from 'new' must be imported first (they are created as new linked objects)
				# for each objecttype, the objects must be posted to api/v1/db/<linked_objecttype>
				#
				# objects from 'updated' must be imported after this, so they can reference the new linked objects
				# these main objects are updated objects that are referenced by the signature (based on base config settings)
				#
				# response from endpoint looks like this:
				# {
				# 	"count": {...},
				# 	"events": [],
				# 	"updated": {
				# 		"<main_objecttype_1>": []
				# 	},
				# 	"new": {
				# 		"<linked_objecttype_1>": [],
				# 		"<linked_objecttype_2>": []
				# 	}
				# }

				# todo: after import was successful, write events to event log -> call @__log_events()


		@__modal = new CUI.Modal
			class: "ez5-zooniverse-importer-modal"
			cancel: true
			onCancel: =>
					@cancel()
			pane:
				header_left: new LocaLabel
					loca_key: "zooniverse.importer.modal.header.label"
				content: @__modalContent
				footer_right: [
					@__importButton
					new CUI.Button
						text: "Cancel"
						onClick: =>
							@cancel()
				]

	cancel: ->
		CUI.confirm
			text: $$("zooniverse.importer.modal.confirm_cancel")
		.done =>
			@__modal.destroy()

	__getUploadFileReader: ->
		new CUI.FileReader
			# todo: add extension filter for csv
			onDone: (fileReader) =>
				try
					csv_data = new CUI.CSVData()
					csv_data.parse(
						text: fileReader.getResult().replaceAll('`', '\\x60').replaceAll('""', '`')
					)
					.done =>
						@__csv_data = csv_data.rows
						@__parseButton.enable()
				catch
					CUI.problem(text: "Error")
					return

	__parseCSV: ->
		url = ez5.pluginManager.getPlugin("easydb-plugin-zooniverse-import").getPluginURL()
		ez5.server
			local_url: url+"/zooniverse_import"
			type: "POST"
			add_token: true
			json_data:
				csv: @__csv_data
				columns_by_id: @__columns_by_id

		.done (result, status, xhr) =>
			console.log "zooniverse_import overview:", result?.count

			# todo: show overview in text area (from 'count')
			#
			# or show a warning if no objects were parsed
			#
			# response from endpoint looks like this:
			# {
			# 	"count": {
			# 		"parsed_rows": 134,
			# 		"parsed_objs": 112,
			# 		"updated": {
			# 			"<main_objecttype_1>": 110
			# 		},
			# 		"updated_total": 110,
			# 		"new": {
			# 			"<linked_objecttype_1>": 50,
			# 			"<linked_objecttype_2>": 80
			# 		},
			# 		"new_total": 130
			# 	},
			# 	"events": [],
			# 	"updated": {...}
			# 	...
			# }

			# only enable import button if there are objects to import
			if result?.count?.new_total > 0 or result?.count?.updated_total > 0
				@__importButton.enable()

			# save events from response, only write events after import was successful
			@__events = result?.events

		.fail (result, status, xhr) =>
			@__importButton.disable()

			console.log "zooniverse_import error:", result
			# todo: save ZOONIVERSE_IMPORT_ERROR event

			# CUI.problem() is not necessary, plugin returns a parsable error (error.user.zooniverse_import)

