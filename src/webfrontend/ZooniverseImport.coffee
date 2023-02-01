class ZooniverseImport extends CUI.Element

	constructor: (@opts={}) ->
		super(@opts)
		@__init()

	initOpts: ->
		super()

	show: ->
		@__modal.show()
		return

	__init: ->
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
						text: fileReader.getResult().replaceAll('""', '`')
					)
					.done =>
						@__csv_data = csv_data.rows
						console.log @__csv_data
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
			json_data: @__csv_data
		.done (result, status, xhr) =>
			console.log result
		.fail () =>
			CUI.problem(text: "Something went wrong when sending the data to the server.")





