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
						path: path

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


	__init: ->
		# plugin needs information about the datamodel
		# api callback can not load all necessary information about the datamodel
		# for each table, get the name by id and the corresponding mask

		@__tables_by_id = {}
		for t in ez5.schema.CURRENT.tables
			@__tables_by_id[t.table_id] = t.name

		@__columns_by_id = {}
		@__parse_fields(ez5.mask.CURRENT.masks, [])

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
			]

		@__importButton = new CUI.Button
			text: $$("zooniverse.importer.import_button.label")
			primary: true
			disabled: true
			onClick: =>
				@__importCSV()

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
			onDone: (fileReader) =>
				try
					csv_data = new CUI.CSVData()
					csv_data.parse(
						text: fileReader.getResult().replaceAll('`', '\\x60').replaceAll('""', '`')
					)
					.done =>
						@__csv_data = csv_data.rows
						@__importButton.enable()
				catch
					CUI.problem(text: "Error")
					return

	__importCSV: ->
		url = ez5.pluginManager.getPlugin("easydb-plugin-zooniverse-import").getPluginURL()
		ez5.server
			local_url: url+"/zooniverse_import"
			type: "POST"
			add_token: true
			json_data:
				csv: @__csv_data
				tables: @__tables_by_id
				columns: @__columns_by_id
		.done (result, status, xhr) =>
			console.log "zooniverse", result
			# todo import objects
		.fail () =>
			CUI.problem(text: "Something went wrong when sending the data to the server.")





