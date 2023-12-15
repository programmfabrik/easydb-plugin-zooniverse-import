# easydb-plugin-zooniverse-import
Plugin to parse CSV-Exports from Zooniverse and update objects.

This plugin can be used in easydb5 and fylr.

## Setup in easydb5

Setup this plugin as an extension plugin in the `easydb-server.yml`:

```yaml
extension:
  plugins:
    - name: easydb-plugin-zooniverse-import
      file: [path]/easydb-plugin-zooniverse-import/build/manifest.yml

plugins:
  enabled+:
    - extension.easydb-plugin-zooniverse-import
```

## Setup in fylr

Add this plugin to fylr by uploading a ZIP file in the Plugin Manager (see https://docs.fylr.io/for-administrators/plugin-manager).

Create the ZIP file by running

```bash
make zip
```

inside the plugin folder. This will create `easydb-plugin-zooniverse-import.zip`.

Add a new plugin, choose type "ZIP" and upload the ZIP file. After this, make sure to enable the plugin.
