PLUGIN_NAME = easydb-plugin-zooniverse-import
PLUGIN_PATH = easydb-plugin-zooniverse-import

INSTALL_FILES = \
	$(WEB)/l10n/cultures.json \
	$(WEB)/l10n/de-DE.json \
	$(WEB)/l10n/en-US.json \
	$(WEB)/l10n/es-ES.json \
	$(WEB)/l10n/it-IT.json \
	$(WEB)/l10n/da-DK.json \
	$(WEB)/l10n/sv-SE.json \
	$(WEB)/l10n/fi-FI.json \
	$(WEB)/l10n/ru-RU.json \
	$(WEB)/l10n/pl-PL.json \
	$(WEB)/l10n/cz-CS.json \
	$(WEB)/ZooniverseImportMenuApp.js \
	$(WEB)/ZooniverseImport.js \
	$(WEB)/ZooniverseImportBaseConfig.js \
	$(WEB)/ZooniverseImport.scss \
	src/server/main.py \
	src/server/util.py \
	src/server/zooniverse.py \
	manifest.yml

#https://docs.google.com/spreadsheets/d/1glXObMmIUd0uXxdFdiPWRZPLCx6qEUaxDfNnmttave4/edit#gid=1425917363
L10N_FILES = l10n/l10n.csv
L10N_GOOGLE_KEY = 1glXObMmIUd0uXxdFdiPWRZPLCx6qEUaxDfNnmttave4
L10N_GOOGLE_GID = 1425917363

COFFEE_FILES = \
	$(WEB)/ZooniverseImportMenuApp.coffee \
	$(WEB)/ZooniverseImport.coffee \
	$(WEB)/ZooniverseImportBaseConfig.coffee

JS = \
	$(WEB)/ZooniverseImportMenuApp.js \
	$(WEB)/ZooniverseImport.js \
	$(WEB)/ZooniverseImportBaseConfig.js

SCSS_FILES = \
	$(WEB)/ZooniverseImport.scss

all: build

include easydb-library/tools/base-plugins.make

build: code css $(L10N) buildinfojson

code: $(JS)

clean: clean-base

wipe: wipe-base

test:
	python3 src/server/test.py
