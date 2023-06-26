class ZooniverseImport extends CUI.Element

	constructor: (@opts={}) ->
		super(@opts)
		@__init()

	initOpts: ->
		super()

	show: ->
		@__modal.show()
		return

	__parse_datamodel_columns: (mask, path, fullname) ->

		if not "fields" of mask
			return

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

				_fname = fullname + '.' + field._column.name
				@__datamodel_columns[_fname] =
					name: field._column.name
					type: field._column.type
				if path.length > 0
					@__datamodel_columns[_fname]["path"] = path

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

				@__parse_datamodel_columns(field._other_table._preferred_mask, new_path, fullname + '.' + field._column.name)

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

				@__parse_datamodel_columns(field.mask, new_path, fullname + '._nested:' + field._other_table.name)

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

		@__datamodel_columns = {}
		for mask in ez5.mask.CURRENT.masks
			@__parse_datamodel_columns(mask, [], mask.table_name_hint)

		@__parseButton = new CUI.Button
			text: $$("zooniverse.importer.modal_content.parse_csv_button.label")
			disabled: true
			onClick: =>
				@__parseCSVBatched()

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
					accept: ".csv,.txt,.text,text/plain,/text/csv"
					icon: "upload"
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

				@__showSplash()

				newObjectPromises = []
				failedImportsObjecttypes = []
				updatedObjectPromises = []

				finishImport = =>
					@__hideSplash()
					if failedImportsObjecttypes.length > 0
						CUI.alert(markdown: true, text: $$("zooniverse.importer.fail_text"))
					else
						if @__events?.length > 0
							for event in @__events
								EventPoller.saveEvent
									type: event.type
									info: event.info_json
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
			onDone: (fileReader) =>
				try
					csv_data = new CUI.CSVData()
					csv_data.parse(
						text: fileReader.getResult().replaceAll('`', '\\x60').replaceAll('""', '`')
					)
					.done =>
						@__csv_data = csv_data.rows
						@__prepareData(csv_data.rows)
						@__parseButton.enable()
				catch
					CUI.problem(text: "Error")
					return

	__prepareData: (rows) ->

		subject_data_index = rows[0].findIndex((el) => el == "subject_data")
		if subject_data_index == -1
			return

		@__preparseData =
			csvHeader : rows[0]
			dataPerSignature: {}
			rowsCount : 0

		rows.splice(0,1)
		getSignature = (row) ->
			try
				jsonString  = row[subject_data_index]?.replace(/['`]/g, '"')
				subjectData = JSON.parse(jsonString)
			catch e
				console.error(e)
			if not subjectData
				return
			for k,v of subjectData
				return v["Filename"]?.replace(/\.[^.]+$/, '');
		 return null

		for row in rows
			signature = getSignature(row)
			if not signature
				continue
			@__preparseData.dataPerSignature[signature] ?= []
			@__preparseData.dataPerSignature[signature].push(row)
			@__preparseData.rowsCount++

		return

	__parseCSVBatched: ->
		url = ez5.pluginManager.getPlugin("easydb-plugin-zooniverse-import").getPluginURL()
		parseAndMergeData = (batch) =>
			dfr = new CUI.Deferred()
			ez5.server(
				local_url: url+"/zooniverse_import"
				type: "POST"
				add_token: true
				json_data:
					csv: batch[0]
					datamodel_columns: @__datamodel_columns
			)
			.fail(dfr.reject)
			.done( (result, status, xhr) =>
				if not @__parsedData
					# We dont have parseData we use the returned by the server
					@__parsedData = result
				else
					# We have parsed data already, we must merge it.
					for objecttype, updatedObjects of result["updated"]
							actualObjects = @__parsedData["updated"]?[objecttype]
							@__parsedData["updated"][objecttype] = if actualObjects then actualObjects.concat(updatedObjects) else updatedObjects
					# for objecttype, newObjects of result["new"]
						# TODO : make the merge of new parsed data

				dfr.resolve()
			)
			return dfr.promise()

		parseBatches = [[@__preparseData.csvHeader]]
		batchIdx = 0
		for signature, rows of @__preparseData.dataPerSignature
			if parseBatches[batchIdx].length > 1000 or parseBatches[batchIdx].length + rows.length > 1000
				batchIdx++
				parseBatches[batchIdx] = [@__preparseData.csvHeader]
			parseBatches[batchIdx] = parseBatches[batchIdx].concat(rows)

		totalCount = 0
		CUI.chunkWork.call(@,
			items: parseBatches
			chunk_size: 1
			call: (batch) =>
				return parseAndMergeData(batch)
		).fail( =>

		)
		return


	__parseCSV: ->
		url = ez5.pluginManager.getPlugin("easydb-plugin-zooniverse-import").getPluginURL()
		ez5.server
			local_url: url+"/zooniverse_import"
			type: "POST"
			add_token: true
			json_data:
				csv: @__csv_data
				datamodel_columns: @__datamodel_columns

		.done (result, status, xhr) =>
			if result?.count

				@__parsedData = result;

				logText = "**#{$$("zooniverse.importer.log.header")}**\n* #{$$("zooniverse.importer.log.parsed_rows")}: #{result.count.parsed_rows}\n* #{$$("zooniverse.importer.log.parsed_objects")}: #{result.count.parsed_objs}\n"

				if not CUI.util.isEmpty(result.count["updated"])
					updatedObjectsText = "\n**#{$$("zooniverse.importer.log.updated_objects")}**\n"
					for k, v of result.count["updated"]
						updatedObjectsText += "* #{k}: #{v}\n"
					logText += updatedObjectsText

					if not CUI.util.isEmpty(result.count["new"])
						newObjectsText = "\n**#{$$("zooniverse.importer.log.new_objects")}**\n"
						for k, v of result.count["new"]
							newObjectsText += "* #{k}: #{v}\n"
						logText += newObjectsText

				else
					logText += "\n**#{$$("zooniverse.importer.log.no_updated_objects")}**\n"

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
			EventPoller.saveEvent
				type: "ZOONIVERSE_IMPORT_ERROR"
				info: result

	__showSplash: ->
		if not @__waitBlock
			@__waitBlock = new CUI.WaitBlock
				element: @__modal.getPane()
		@__waitBlock.show()

	__hideSplash: ->
		@__waitBlock?.hide()


