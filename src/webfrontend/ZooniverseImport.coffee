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
			content: [
				new CUI.Label
					text: "Please upload a valid CSV and press import"
			,
				new CUI.FileUploadButton
					fileUpload: @__getUploadFileReader()
					text: "Upload CSV"
					multiple: false
			]

		@__importButton = new CUI.Button
			text: "Import"
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
			text: "Are you sure you want to close the import?"
		.done =>
			@__modal.destroy()

	__getUploadFileReader: ->
		new CUI.FileReader
			onDone: (fileReader) =>
				try
					@__csv_data = fileReader.getResult()
					console.log @__csv_data
					@__importButton.enable()
				catch
					CUI.problem(text: "Error")
					return

	__importCSV: ->
		url = ez5.pluginManager.getPlugin("easydb-plugin-zooniverse-import").getBaseURL()
		ez5.server
			local_url: url+"/zooniverse_import"
			type: "POST"
			add_token: true
			data:
				csvdata: @__csv_data
		.done (result, status, xhr) =>
			console.log result
		.fail () =>
			CUI.problem(text: "Something went wrong when sending the data to the server.")





