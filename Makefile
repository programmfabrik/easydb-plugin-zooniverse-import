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
	$(WEB)/easydb-plugin-zooniverse-import.js \
	$(WEB)/easydb-plugin-zooniverse-import.css \
	src/server/main.py \
	src/server/mapping.py \
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
	$(WEB)/easydb-plugin-zooniverse-import.js \

SCSS_FILES = \
	$(WEB)/ZooniverseImport.scss

all: build

include easydb-library/tools/base-plugins.make

build: code css $(L10N) buildinfojson ## build code, creates build folder
	cp build/webfrontend/ZooniverseImport.scss build/webfrontend/easydb-plugin-zooniverse-import.css
	rm build/webfrontend/*.coffee.js
	rm build/webfrontend/*.scss
	cp -r src/server build
	cp manifest.master.yml build/manifest.yml
	cp l10n/l10n.csv build/webfrontend/l10n

code: $(JS)

clean: clean-base
	rm $(PLUGIN_NAME).zip || true

wipe: wipe-base

test: build
	python3 build/server/test.py

zip: build ## build zip file for publishing (fylr only)
	rm $(PLUGIN_NAME).zip || true
	rm -r $(PLUGIN_NAME) || true
	cp -r build $(PLUGIN_NAME)
	zip $(PLUGIN_NAME).zip -x *.pyc -x */__pycache__/* -r $(PLUGIN_NAME)/
	rm -rf $(PLUGIN_NAME)
