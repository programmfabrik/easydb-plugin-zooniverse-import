# encoding: utf-8

import sys
import json

import util

from fylr_lib_plugin_python3 import util as fylr_util


def main():
    try:
        # read info json from 1st parameter
        if len(sys.argv) < 2:
            raise Exception('missing info.json as 1st parameter')

        info_json = json.loads(sys.argv[1])
        api_url = util.get_json_value(info_json, 'api_url', True) + '/api/v1'
        access_token = util.get_json_value(info_json, 'api_user_access_token', True)

        # read POST body from stdin
        post_body = sys.stdin.read()
        datamodel_columns = util.parse_datamodel(post_body)

        # load the base config (api/v1/config/system)
        config_languages = fylr_util.get_config_from_api(
            api_url=api_url,
            access_token=access_token,
            path='system/config/languages/database',
        )
        languages = []
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
        plugin_config = util.get_json_value(
            info_json,
            'config.plugin.easydb-plugin-zooniverse-import.config.zooniverse_import_mappings.mappings',
        )
        mappings = util.load_mappings(plugin_config, datamodel_columns)

        stats = util.import_data(
            post_body,
            mappings,
            languages,
            api_url,
            access_token,
        )

        fylr_util.return_response(stats)

    except Exception as e:
        fylr_util.return_error_response(str(e))


if __name__ == '__main__':
    main()
