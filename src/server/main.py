# coding=utf8

import util

PLUGIN_NAME = 'easydb-plugin-zooniverse-import'


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger(PLUGIN_NAME)
    logger.debug('debugging is activated')

    easydb_context.register_callback('api', {
        'name': 'zooniverse_import',
        'callback': 'api_zooniverse_import'
    })


def api_zooniverse_import(easydb_context, parameters):
    try:
        logger = easydb_context.get_logger(PLUGIN_NAME)
        config = easydb_context.get_config()

        post_body = util.get_json_value(parameters, 'body', True)

        columns_by_id = util.parse_datamodel(post_body, logger)

        # load activated database languages from base config
        languages = util.get_json_value(config, 'base.system.languages.database')
        if not isinstance(languages, list) or len(languages) < 1:
            languages = ['en-US']

        # load mappings from base config
        plugin_config = util.get_json_value(config, 'base.system.zooniverse_import_mappings.mappings')
        mappings = util.load_mappings(plugin_config, columns_by_id, logger)

        stats = util.import_data(
            post_body,
            mappings,
            languages,
            None,  # api_url not needed
            None,  # access_token not needed
            easydb_context,
            logger,
        )

        return util.json_response(stats, minify=True)

    except Exception as e:
        return util.json_error_response('could not parse zooniverse data: {0}'.format(e), logger)
