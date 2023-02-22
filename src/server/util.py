# coding=utf8

import json
import sys
import traceback
import re


def handle_exceptions(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_info = sys.exc_info()
            stack = traceback.extract_stack()
            tb = traceback.extract_tb(exc_info[2])
            full_tb = stack[:-1] + tb
            exc_line = traceback.format_exception_only(*exc_info[:2])

            trace = [str(repr(e))] + traceback.format_list(full_tb) + exc_line

            print('\n'.join(trace))

    return func_wrapper


def dumpjs(js, indent=4):
    return json.dumps(js, indent=indent)


def get_json_value(js, path, expected=False, split_char='.'):

    current = js
    path_parts = []
    current_part = ''

    for i in range(len(path)):
        if path[i] != split_char:
            current_part += path[i]
            if i == len(path) - 1:
                path_parts.append(current_part)
            continue

        if i > 0 and path[i - 1] == '\\':
            current_part += path[i]
            continue

        if len(current_part) > 0:
            path_parts.append(current_part)
            current_part = ''

    for path_part in path_parts:
        path_part = path_part.replace('\\' + split_char, split_char)

        if not isinstance(current, dict) or path_part not in current:
            if expected:
                raise Exception('expected: ' + path_part)
            else:
                return None

        current = current[path_part]

    return current


# ---------------------


def json_response(js, statuscode=200, minify=False):
    return {
        'status_code': statuscode,
        'body': dumpjs(js, indent=None if minify else 4),
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        }
    }


def json_error_response(msg, logger=None):
    error = {
        'realm': 'user',
        'code': 'error.user.zooniverse_import',
        'parameters': {
                'description': msg
        }
    }

    if logger is not None:
        logger.error(dumpjs(error))

    return json_response(error, statuscode=400)


# ---------------------


def load_mappings(config, columns_by_id, logger):
    plugin_config = get_json_value(config, 'base.system.zooniverse_import_mappings.mappings')
    logger.debug('plugin_config: {0}'.format(dumpjs(plugin_config)))

    mappings = {}

    if not isinstance(plugin_config, list):
        return mappings

    for m in plugin_config:
        enabled = get_json_value(m, 'enabled')
        if not isinstance(enabled, bool):
            continue
        if not enabled:
            continue

        update_objecttype = get_json_value(m, 'update_objecttype')
        if not isinstance(update_objecttype, str):
            continue
        if len(update_objecttype) < 1:
            continue

        match_column = get_json_value(m, 'match_column')
        if not isinstance(match_column, str):
            continue
        if not match_column.startswith('{0}.'.format(update_objecttype)):
            continue
        m['match_column'] = match_column[len(update_objecttype) + 1:]

        for k in m.keys():
            if not k.startswith('update_column_'):
                continue

            update_column = m[k]
            if update_column not in columns_by_id:
                continue

            # logger.debug('column {0}: {1}'.format(update_column, dumpjs(columns_by_id[update_column])))
            m[k] = columns_by_id[update_column]

        mappings[update_objecttype] = m

    return mappings

# ---------------------------------


def get_user_id_from_context(easydb_context):
    user_id = get_json_value(easydb_context.get_session(), 'user.user._id')
    if not isinstance(user_id, int):
        raise Exception('Could not get user id from session')
    return user_id


@handle_exceptions
def load_objects_by_signature(easydb_context, objecttype, match_column, signatures, logger):
    limit = 1000
    offset = 0

    affected_objects = {}

    user_id = get_user_id_from_context(easydb_context)

    has_more = True
    while has_more:
        query = {
            'offset': 0,
            'limit': limit,
            'search': [
                {
                    'bool': 'must',
                    'type': 'in',
                    'fields': [
                        '{0}.{1}'.format(objecttype, match_column)
                    ],
                    'in': signatures[offset:offset + limit]
                }
            ],
            'format': 'long',
            'objecttypes': [
                objecttype
            ]
        }
        offset += limit
        has_more = offset < len(signatures)

        # logger.debug('[load_objects_by_signature] search query: {0}'.format(dumpjs(query)))

        result_objects = get_json_value(
            easydb_context.search('user', user_id, query),
            'objects')
        if not isinstance(result_objects, list):
            raise Exception('Could not parse objects array from search result')

        # logger.debug('[load_objects_by_signature] search response: {0}'.format(dumpjs(result_objects)))

        for obj in result_objects:
            signatur = get_json_value(obj, '{0}.{1}'.format(objecttype, match_column))
            if not isinstance(signatur, str):
                continue

            obj = get_json_value(obj, objecttype)
            if not isinstance(obj, dict):
                continue

            affected_objects[signatur] = obj

    return affected_objects


# -----------------------

@handle_exceptions
def create_new_linked_objects(easydb_context, unique_linked_object_values, logger, languages):
    new_linked_objects = {}
    count_objects = {}

    for objecttype in unique_linked_object_values:
        new_linked_objects[objecttype] = []
        count = 0

        for match_column in unique_linked_object_values[objecttype]:
            unique_values = unique_linked_object_values[objecttype][match_column]
            logger.debug('[create_new_linked_objects] field: {0}.{1}, values: {2}'.format(objecttype, match_column, unique_values))

            existing_objects = load_objects_by_signature(
                easydb_context,
                objecttype,
                match_column,
                unique_values,
                logger
            )
            logger.debug('[create_new_linked_objects] existing objects for values: {0}' .format(existing_objects.keys()))

            # for all unique values, skip those which are found and create new objects for all missing values
            for v in unique_values:
                if v in existing_objects:
                    continue

                # create a new object
                new_linked_objects[objecttype].append(
                    build_object(objecttype, {
                        '_version': 1,
                        match_column: v
                    }, languages))
                count += 1

        count_objects[objecttype] = count

    return new_linked_objects, count_objects

# -----------------------


def build_object(objecttype, obj, languages):
    commments_l10n = {
        'de-DE': 'Bearbeitung erfolgte durch das Zooniverse Import Plugin',
        'en-US': 'Object was edited by the Zooniverse Import Plugin',
    }
    comment = commments_l10n['en-US']
    if len(languages) > 0 and languages[0] in commments_l10n:
        comment = commments_l10n[languages[0]]

    return {
        '_comment': comment,
        '_mask': '_all_fields',
        '_objecttype': objecttype,
        objecttype: obj,
    }


def format_date(value):
    try:
        m = re.match(
            r'^\d{4}(-\d{2}(-\d{2}((T| )(\d{2}(:\d{2}(:\d{2}((\+|-)\d{1,2}:\d{2}){0,1}){0,1}){0,1}){0,1}){0,1}){0,1}){0,1}$',
            value
        )
        if m is None:
            return None
        return {
            'value': value
        }
    except:
        return None


def split_value(value):

    res = []
    if isinstance(value, str):
        parts = re.split(',|;', value)
        for p in parts:
            p = p.strip()
            if len(p) < 1:
                continue
            res.append(p)

        if len(res) < 1:
            return None
        return res

    if isinstance(value, list):
        for v in value:
            parts = re.split(',|;', v)
            for p in parts:
                p = p.strip()
                if len(p) < 1:
                    continue
                res.append(p)

        if len(res) < 1:
            return None
        return res

    return None


# ---------------------------


def parse_datamodel(data, logger):

    if data is None:
        return {}

    js = None
    try:
        js = json.loads(data)
    except:
        return {}

    columns_by_id = get_json_value(js, 'columns_by_id')
    if not isinstance(columns_by_id, dict):
        return {}

    return columns_by_id
