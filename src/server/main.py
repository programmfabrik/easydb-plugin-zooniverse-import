# coding=utf8

import util
import zooniverse

PLUGIN_NAME = 'easydb-plugin-zooniverse-import'
ENDPOINT_ZOONIVERSE_IMPORT = 'zooniverse_import'


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger(PLUGIN_NAME)
    logger.debug('debugging is activated')

    easydb_context.register_callback('api', {
        'name': ENDPOINT_ZOONIVERSE_IMPORT,
        'callback': 'api_zooniverse_import'
    })

    logger.info('registered api callback {1}, endpoint: <server>/api/plugin/extension/{0}/{1}'.format(
        PLUGIN_NAME, ENDPOINT_ZOONIVERSE_IMPORT))


@util.handle_exceptions
def api_zooniverse_import(easydb_context, parameters):
    logger = easydb_context.get_logger(PLUGIN_NAME)

    try:
        content = zooniverse.parse_data(parameters['body'], logger)
        if content is None:
            return util.json_error_response('could not parse body'.format())
        return util.json_response(content)

    except Exception as e:
        return util.json_error_response('could not parse body: {0}'.format(str(e)))
