# encoding: utf-8

import sys
import json

import util

from fylr_lib_plugin_python3 import util as fylr_util

if __name__ == '__main__':

    try:
        # read info json from 1st parameter
        if len(sys.argv) < 2:
            raise Exception('missing info.json as 1st parameter')

        info_json = json.loads(sys.argv[1])
        api_url = util.get_json_value(info_json, 'api_url', True)
        access_token = util.get_json_value(info_json, 'api_user_access_token', True)

        # read POST body from stdin
        post_body = sys.stdin.read()
        columns_by_id = util.parse_datamodel(post_body)

        # load activated database languages from base config
        languages = []
        config_languages = util.get_json_value(info_json, 'config.system.config.languages.database')
        for e in config_languages:
            lang = util.get_json_value(e, 'value')
            if not isinstance(lang, str):
                continue
            if len(lang) < 1:
                continue
            languages.append(lang)
        if len(languages) < 1:
            languages = ['en-US']

        # load mappings from base config
        plugin_config = util.get_json_value(info_json, 'config.plugin.easydb-plugin-zooniverse-import.config.zooniverse_import_mappings.mappings')
        mappings = util.load_mappings(plugin_config, columns_by_id)

        fylr_util.write_tmp_file('zooniverse.json', [
            'api_url', util.dumpjs(api_url),
            'access_token', util.dumpjs(access_token),
            'columns_by_id', util.dumpjs(columns_by_id),
            'plugin_config', util.dumpjs(plugin_config),
            'mappings', util.dumpjs(mappings),
            'languages', util.dumpjs(languages),
        ], new_file=True)

        stats = util.import_data(
            post_body,
            mappings,
            languages,
            api_url + '/api/v1',
            access_token,
        )

        fylr_util.return_response(stats)

    except Exception as e:
        fylr_util.return_error_response(str(e))
