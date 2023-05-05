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

		@__overviewText = new CUI.MultilineLabel
			text: ""
			markdown: true
			class: "ez5-zooniverse-importer-log-label"

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
			,
				@__overviewText
			]

		@__importButton = new CUI.Button
			text: $$("zooniverse.importer.import_button.label")
			primary: true
			disabled: true
			onClick: =>

				if not @__parsedData
					return

				newObjectPromises = []
				failedImportsObjecttypes = []
				updatedObjectPromises = []

				finishImport = =>
					if failedImportsObjecttypes.length > 0
						CUI.alert(markdown: true, text: $$("zooniverse.importer.fail_text"))
					else
						CUI.alert(markdown: true, text: $$("zooniverse.importer.success_text"))
						@clean()

				importUpdates = =>
					if @__parsedData["updated"]?.length == 0
						finishImport()
					else
						for ot_name, objects of @__parsedData["updated"]
							do(ot_name) =>
								updatedObjectPromises.push(
									CUI.chunkWork.call(@,
										items: objects
										chunk_size: 1000
										call: (items) =>
											return ez5.api.db(
												type: "POST"
												api: '/'+ot_name
												json_data: items
											)
									).fail( =>
										failedImportsObjecttypes.push(ot_name)
									)
								)
						CUI.whenAll(updatedObjectPromises).done(=>
							finishImport()
						)

				if not @__parsedData["new"].length == 0
					importUpdates()
				else
					# ez5 can handle multiple objecttypes post in parallel?
					for ot_name, objects of @__parsedData["new"]
						do(ot_name) =>
							newObjectPromises.push(
								CUI.chunkWork.call(@,
									items: objects
									chunk_size: 1000
									call: (items) =>
										return ez5.api.db(
											type: "POST"
											api: '/'+ot_name
											json_data: items
										)
								).fail( =>
									failedImportsObjecttypes.push(ot_name)
								)
						)
					CUI.whenAll(newObjectPromises).done( =>
						importUpdates()
					)


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

	clean: ->
		@__setOverviewText("")
		delete(@__csv_data)
		@__parseButton.disable()
		@__importButton.disable()

	__setOverviewText: (text) ->
		@__overviewText.setText(text)
		CUI.Events.trigger
			node: @__modal
			type: "content-resize"


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
			if result?.count

				@__parsedData = result;

				logText = "#{$$("zooniverse.importer.log.header")} \n
					#{$$("zooniverse.importer.log.parsed_rows")}: #{result.count.parsed_rows} \n
					#{$$("zooniverse.importer.log.parsed_objects")} : #{result.count.parsed_objs} \n"

				if not CUI.util.isEmpty(result.count["updated"])
					updatedObjectsText = "**#{$$("zooniverse.importer.log.updated_objects")}** : \n"
					for k, v of result.count["updated"]
						updatedObjectsText += "\t #{k} : #{v} \n"
					logText += updatedObjectsText

				if not CUI.util.isEmpty(result.count["new"])
					newObjectsText = "**#{$$("zooniverse.importer.log.new_objects")}** \n"
					for k, v of result.count["new"]
						newObjectsText += "\t #{k} : #{v} \n"
					logText += newObjectsText

				@__setOverviewText(logText)

			else
				CUI.alert(text: "No objects could be parsed.")

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

