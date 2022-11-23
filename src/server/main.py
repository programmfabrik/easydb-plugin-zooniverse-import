# coding=utf8

import util
import zooniverse

PLUGIN_NAME = 'easydb-plugin-zooniverse-import'
LOGGER_NAME = 'pf.plugin.extension.' + PLUGIN_NAME
ENDPOINT_ZOONIVERSE_IMPORT = 'zooniverse_import'


def easydb_server_start(easydb_context):
    logger = easydb_context.get_logger(LOGGER_NAME)

    easydb_context.register_callback('api', {
        'name': ENDPOINT_ZOONIVERSE_IMPORT,
        'callback': 'api_zooniverse_import'
    })

    logger.info('registered api callback {1}, endpoint: <server>/api/plugin/extension/{0}/{1}'.format(
        PLUGIN_NAME, ENDPOINT_ZOONIVERSE_IMPORT))


def api_zooniverse_import(easydb_context, parameters):

    logger = easydb_context.get_logger(LOGGER_NAME)

    PARAMS_KEY = 'query_string_parameters'
    CSV_KEY = 'csvdata'
    if not PARAMS_KEY in parameters:
        err = '{0} missing in request'.format(PARAMS_KEY)
        logger.warn(err)
        util.json_error_response(err)
    if not CSV_KEY in parameters[PARAMS_KEY]:
        err = '{0}.{1} missing in request'.format(PARAMS_KEY, CSV_KEY)
        logger.warn(err)
        util.json_error_response(err)

    content = None
    try:
        csv_data = ''.join(parameters[PARAMS_KEY][CSV_KEY]).splitlines()
        content = zooniverse.parse_csv(csv_data, logger)
    except Exception as e:
        return util.json_error_response('could not parse {0}.{1}: {2}'.format(PARAMS_KEY, CSV_KEY, str(e)))
    if content is None:
        return util.json_error_response('could not parse {0}.{1}'.format(PARAMS_KEY, CSV_KEY))

    return util.json_response(content)
