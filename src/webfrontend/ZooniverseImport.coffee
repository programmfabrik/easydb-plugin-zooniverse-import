class ZooniverseImport extends CUI.Element

	constructor: (@opts={}) ->
		super(@opts)
		@__init()

	initOpts: ->
		super()

	show: ->
		@__modal.show()
		return

	# __init: ->
	# 	@__modal = @__buildModal()
	# 	return

	# __buildModal: ->

	# 	return new CUI.Modal

	# 	# TODO: Button "load_csv" -> open file dialog, select csv file, store content of csv file

	# 	# TODO: Button "post_csv_to_api" -> perform POST request with content of csv file

