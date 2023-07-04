# coding=utf8

import json
import re
import requests
from datetime import datetime, timedelta

import zooniverse
import mapping

from fylr_lib_plugin_python3 import util as fylr_util


# ---------------------
__times = {}


def time_now(k):
    __times[k] = datetime.now()
    return __times[k]


def time_diff(k):
    if k not in __times:
        return None

    sec = timedelta.total_seconds(datetime.now() - __times[k])
    return sec * 1000.0

# ---------------------


def debug(line, logger):
    if logger is not None:
        logger.debug(line)


def info(line, logger):
    if logger is not None:
        logger.info(line)


def warn(line, logger):
    if logger is not None:
        logger.warn(line)


def error(line, logger):
    if logger is not None:
        logger.error(line)

# ---------------------


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

    error(dumpjs(error), logger)

    return json_response(error, statuscode=400)


# ---------------------


def load_mappings(plugin_config, datamodel_columns, logger=None):
    # debug('plugin_config: {0}'.format(dumpjs(plugin_config)), logger)

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
            if update_column not in datamodel_columns:
                continue

            # debug('column {0}: {1}'.format(update_column, dumpjs(datamodel_columns[update_column])), logger)
            m[k] = datamodel_columns[update_column]

        mappings[update_objecttype] = m

    return mappings

# ---------------------------------


def __search_fylr(api_url, token, query) -> dict:
    resp = requests.post(
        api_url + '/search',
        headers={
            'Authorization': 'Bearer ' + token,
        },
        data=dumpjs(query))

    if resp.status_code != 200:
        raise Exception('search error: status: {0}, response: {1}'.format(resp.status_code, resp.text))

    try:
        result = json.loads(resp.text)
    except Exception as e:
        raise Exception('search error: could not parse search response {0}: {1}'.format(resp.text, str(e)))

    return result


def __search_ez5(easydb_context, user_id, query):
    return easydb_context.search('user', user_id, query)


def __get_user_id_from_context(easydb_context):
    user_id = get_json_value(easydb_context.get_session(), 'user.user._id')
    if not isinstance(user_id, int):
        raise Exception('Could not get user id from session')
    return user_id


# ---------------------------------

def __load_objects_by_signature(objecttype, match_column, signatures, api_url, token, easydb_context=None, logger=None):
    limit = 1000
    offset = 0

    affected_objects = {}

    # only needed for easydb5, do not repeatedly load the session
    user_id = __get_user_id_from_context(easydb_context) if easydb_context is not None else None

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

        if easydb_context is not None:
            # for easydb5
            result = __search_ez5(easydb_context, user_id, query)
        else:
            # for fylr
            result = __search_fylr(api_url, token, query)

        result_objects = get_json_value(result, 'objects')

        if not isinstance(result_objects, list):
            raise Exception('Could not parse objects array from search result')

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

def __create_new_linked_objects(unique_linked_object_values, languages, api_url, token, easydb_context=None, logger=None):
    new_linked_objects = {}
    count_objects = {}

    for objecttype in unique_linked_object_values:
        new_linked_objects[objecttype] = []
        count = 0

        for match_column in unique_linked_object_values[objecttype]:
            unique_values = unique_linked_object_values[objecttype][match_column]
            # debug('[create_new_linked_objects] field: {0}.{1}, values: {2}'.format(objecttype, match_column, unique_values), logger)

            existing_objects = __load_objects_by_signature(
                objecttype,
                match_column,
                unique_values,
                api_url,
                token,
                easydb_context,
                logger
            )
            # debug('[create_new_linked_objects] existing objects for values: {0}' .format(existing_objects.keys()), logger)

            # for all unique values, skip those which are found and create new objects for all missing values
            for v in unique_values:
                if v in existing_objects:
                    continue

                # create a new object
                new_linked_objects[objecttype].append(
                    __build_object(objecttype, {
                        '_version': 1,
                        match_column: v
                    }, languages))
                count += 1

        count_objects[objecttype] = count

    return new_linked_objects, count_objects

# -----------------------


def __build_object(objecttype, obj, languages):
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


def __check_datetime(value):
    try:
        m = re.match(
            r'^\d{4}(-\d{2}(-\d{2}((T| )(\d{2}(:\d{2}(:\d{2}((\+|-)\d{1,2}:\d{2}){0,1}){0,1}){0,1}){0,1}){0,1}){0,1}){0,1}$',
            value
        )
        return m is not None
    except:
        return False


def format_datetime(value):
    if not __check_datetime(value):
        return None

    return {
        'value': value
    }


def format_date(value):
    if not __check_datetime(value):
        return None

    return {
        'value': re.split(' |T', value)[0].strip()
    }


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


def parse_datamodel(data, logger=None):

    if data is None:
        return {}

    js = None
    try:
        js = json.loads(data)
    except:
        return {}

    datamodel_columns = get_json_value(js, 'datamodel_columns')
    if not isinstance(datamodel_columns, dict):
        return {}

    return datamodel_columns


# ---------------------------

def import_data(post_body, mappings, languages, api_url, token, easydb_context=None, logger=None) -> dict:

    start_all = time_now('start_all')
    time_now('start_parse_data')
    collected_objects, stats = zooniverse.parse_data(post_body, logger)
    if not isinstance(collected_objects, dict):
        raise Exception('could not parse body')

    stats['updated'] = {}
    stats['new'] = {}
    stats['times'] = {
        'start': str(start_all),
        'parse_data': time_diff('start_parse_data')
    }
    stats['count']['new'] = {}
    stats['count']['new_total'] = 0
    stats['count']['updated'] = {}
    stats['count']['updated_total'] = 0
    stats['events'] = []

    if collected_objects == {}:
        warn('no zooniverse data was parsed from csv', logger)
        return stats

    unique_linked_object_values = {}

    time_now('start_apply_mapping')
    for objecttype in mappings:
        ot_mapping = mappings[objecttype]
        match_column = get_json_value(ot_mapping, 'match_column')
        if not isinstance(match_column, str):
            continue

        count_updated = 0

        # load objects with the collected signatures
        affected_objects = __load_objects_by_signature(
            objecttype,
            match_column,
            list(collected_objects.keys()),
            api_url,
            token,
            easydb_context,
            logger
        )

        event = {
            'type': 'ZOONIVERSE_IMPORT_UPDATE',
            'info_json': {
                'objecttype': objecttype,
                'objects': []
            }
        }

        # iterate over objects, update objects with mapped data
        updated_objects = []
        for signatur in affected_objects:
            if signatur not in collected_objects:
                debug('signatur {0} not in collected objects -> skip'.format(signatur), logger)
                continue

            obj = affected_objects[signatur]
            zooniverse_data = collected_objects[signatur]

            for user_name in zooniverse_data:
                for created_at in zooniverse_data[user_name]:

                    top_level_field_user = mapping.apply(
                        obj=obj,
                        unique_linked_object_values=unique_linked_object_values,
                        mapping=ot_mapping,
                        column_name='update_column_user_name',
                        value=user_name,
                        signatur=signatur,
                        languages=languages,
                        logger=logger,
                    )
                    top_level_field_created = mapping.apply(
                        obj=obj,
                        unique_linked_object_values=unique_linked_object_values,
                        mapping=ot_mapping,
                        column_name='update_column_created_at',
                        value=created_at,
                        signatur=signatur,
                        languages=languages,
                        logger=logger,
                    )

                    # user_name and created_at are grouped if they are mapped into the same nested table
                    if top_level_field_user is not None and top_level_field_user.startswith('_nested:') and top_level_field_user == top_level_field_created:
                        # take columns from last 2 rows and merge them into one row
                        if len(obj[top_level_field_user]) > 1:
                            last_entry = obj[top_level_field_user][-1]
                            del obj[top_level_field_user][-1]
                            for k in last_entry:
                                obj[top_level_field_user][-1][k] = last_entry[k]

                    for k in zooniverse_data[user_name][created_at]:
                        mapping.apply(
                            obj=obj,
                            unique_linked_object_values=unique_linked_object_values,
                            mapping=ot_mapping,
                            column_name='update_column_{}'.format(k.lower()),
                            value=zooniverse_data[user_name][created_at][k],
                            signatur=signatur,
                            languages=languages,
                            logger=logger,
                        )

            id = get_json_value(obj, '_id')
            if not isinstance(id, int):
                continue

            version = get_json_value(obj, '_version')
            if not isinstance(version, int):
                continue
            obj['_version'] = version + 1

            updated_objects.append(__build_object(objecttype, obj, languages=languages))
            count_updated += 1

            event['info_json']['objects'].append({
                '_id': id,
                '_version': version + 1,
                'match_column': match_column,
                'unique_value': signatur
            })

        if len(updated_objects) < 1:
            continue

        stats['updated'][objecttype] = updated_objects
        stats['count']['updated'][objecttype] = count_updated
        stats['count']['updated_total'] += count_updated

        event['info_json']['objects'] = sorted(event['info_json']['objects'], key=lambda o: o['_id'])
        stats['events'].append(event)

    stats['times']['apply_mapping'] = time_diff('start_apply_mapping')

    time_now('start_create_new_linked_objects')
    new_linked_objects, count_new = __create_new_linked_objects(
        unique_linked_object_values,
        languages,
        api_url,
        token,
        easydb_context,
        logger,
    )
    stats['new'] = new_linked_objects
    stats['count']['new'] = count_new
    stats['times']['create_new_linked_objects'] = time_diff('start_create_new_linked_objects')

    for objecttype in unique_linked_object_values:
        event = {
            'type': 'ZOONIVERSE_IMPORT_INSERT',
            'info_json': {
                'objecttype': objecttype,
                'unique_column': match_column,
                'unique_values': []
            }
        }

        for unique_column in unique_linked_object_values[objecttype]:
            for v in sorted(unique_linked_object_values[objecttype][unique_column]):
                event['info_json']['unique_values'].append(v)

        stats['events'].append(event)

    count_new_total = 0
    for ot in count_new:
        count_new_total += count_new[ot]
    stats['count']['new_total'] = count_new_total

    stats['times']['total'] = time_diff('start_all')

    debug('overview: count: {0}'.format(dumpjs(stats['count'])), logger)
    debug('overview: times: {0}'.format(dumpjs(stats['times'])), logger)

    return stats
