# coding=utf8

import util


def __linked_object(elem, fieldname, value, unique_linked_object_values):
    link_ot = util.get_json_value(elem, 'objecttype')
    if not isinstance(link_ot, str) or len(link_ot) < 1:
        raise Exception('invalid path: link.objecttype invalid: ' + str(link_ot))

    if not link_ot in unique_linked_object_values:
        unique_linked_object_values[link_ot] = {}
    if not fieldname in unique_linked_object_values[link_ot]:
        unique_linked_object_values[link_ot][fieldname] = []
    if value not in unique_linked_object_values[link_ot][fieldname]:
        unique_linked_object_values[link_ot][fieldname].append(value)

    return {
        '_mask': '_all_fields',
        '_objecttype': link_ot,
        link_ot: {
            'lookup:_id': {
                fieldname: value
            }
        }
    }


def __build_recursive_entry(path, fieldname, value, unique_linked_object_values, logger=None):

    if fieldname is None or len(fieldname) < 1:
        return None, None

    if value is None:
        return None, None

    if path is None or len(path) < 1:
        return value, fieldname

    elem = path[0]
    path_type = util.get_json_value(elem, 'type')
    path_name = util.get_json_value(elem, 'name')

    if path_type == 'link':
        try:
            link = __linked_object(elem, fieldname, value, unique_linked_object_values)
            return link, path_name
        except Exception as e:
            util.warn('mapping: could not create link: ' + str(e), logger)
            return None, None

    if path_type == '_nested':
        sub_elem, sub_name = __build_recursive_entry(path[1:], fieldname, value, unique_linked_object_values, logger)
        return [{sub_name: sub_elem}], path_type + ':' + path_name

    raise Exception('invalid path type ' + str(path_type))


def __is_in_nested(entry, nested: list, linked_ot_path: dict, logger=None) -> bool:
    # direct match for simple values (strings, dicts) in list

    if entry in nested:
        return True

    # complex match, necessary to compare newly created linked objects and existing linked objects (dicts are not equal)

    if not 'name' in linked_ot_path:
        return False
    if not 'objecttype' in linked_ot_path:
        return False

    name = linked_ot_path['name']
    ot = linked_ot_path['objecttype']

    lookup = util.get_json_value(entry, '{0}.{1}.lookup:_id'.format(name, ot))
    if len(lookup) != 1:
        return False

    value = lookup[list(lookup.keys())[0]]

    for e in nested:
        standard = util.get_json_value(e, '{0}._standard.1.text'.format(name))
        if not isinstance(standard, dict):
            continue
        for lang in standard:
            if standard[lang] == value:
                return True

    return False


def apply(obj, unique_linked_object_values, mapping, column_name, value, signatur, languages, group_into_nested=None, logger=None):
    if value is None:
        return

    fieldname = util.get_json_value(mapping, column_name + '.name')
    if fieldname is None:
        return

    fieldtype = util.get_json_value(mapping, column_name + '.type')
    if fieldtype is None:
        return

    path = util.get_json_value(mapping, column_name + '.path')
    if path is None:
        path = []

    split_value = util.get_json_value(mapping, 'split_' + column_name)
    if not isinstance(split_value, bool):
        split_value = False

    # do not split if no nested
    if len(path) < 1:
        split_value = False
    elif len(path) < 2:
        if util.get_json_value(path[-1], 'type') != '_nested':
            split_value = False
    else:
        if util.get_json_value(path[-1], 'type') != '_nested' and util.get_json_value(path[-2], 'type') != '_nested':
            split_value = False

    is_list = False
    if isinstance(value, list):
        is_list = True
        if len(value) < 1:
            return

    if split_value:
        value = util.split_value(value)
        if isinstance(value, list):
            is_list = True
            if len(value) < 1:
                return

    formatted_value = []

    if not is_list:
        formatted_value = [str(value)]
    else:
        formatted_value = value

    if fieldtype in ['text_l10n', 'text_l10n_oneline']:
        _fv = []
        for fv in formatted_value:
            _v = {}
            for lang in languages:
                _v[lang] = fv
            _fv.append(_v)
        formatted_value = _fv

    elif fieldtype in ['date']:
        _fv = []
        for fv in formatted_value:
            _fv.append(util.format_date(value))
        formatted_value = _fv

    elif fieldtype in ['datetime']:
        _fv = []
        for fv in formatted_value:
            _fv.append(util.format_datetime(value))
        formatted_value = _fv

    # util.debug('[mapping.apply] [{0}] value: {1} => formatted: {2}'.format(signatur, value, formatted_value),logger)

    if len(formatted_value) < 1:
        return

    if len(path) < 1:
        # simple field on top level of the object
        obj[fieldname] = formatted_value[0]
        util.debug('[mapping.apply] [{0}] inserted/replaced {1}: {2}'.format(signatur, fieldname, obj[fieldname]), logger)
        return

    # field is in path (nested tables and/or linked objects)
    for v in formatted_value:
        entry, entry_fieldname = __build_recursive_entry(path, fieldname, v, unique_linked_object_values, logger)
        if entry is None:
            continue

        # insert new value
        if not entry_fieldname in obj:
            obj[entry_fieldname] = entry
            util.debug('[mapping.apply] [{0}] inserted {1} with {2}'.format(signatur, entry_fieldname, entry), logger)
            continue

        # check the existing value (nested vs. single value)
        if isinstance(obj[entry_fieldname], list):
            if not isinstance(entry, list):
                entry = [entry]
            for e in entry:
                if __is_in_nested(e, obj[entry_fieldname], path[-1], logger):
                    continue

                obj[entry_fieldname].append(e)
                util.debug('[mapping.apply] [{0}] appended to {1}: {2}'.format(signatur, entry_fieldname, e), logger)

    # if there is a name of a nested table given
    if group_into_nested is None:
        return

    nested = util.get_json_value(obj, group_into_nested)
    if not isinstance(nested, list):
        return

    grouped_nested = {}
    for row in nested:
        for k in row:
            v = row[k]
            if v is None:
                continue
            if k not in grouped_nested:
                grouped_nested[k] = []
            if v in grouped_nested[k]:
                continue
            grouped_nested[k].append(v)

    for k in grouped_nested:
        if len(grouped_nested[k]) == 0:
            grouped_nested[k] = None
            continue
        if len(grouped_nested[k]) == 1:
            grouped_nested[k] = grouped_nested[k][0]
            continue
        try:
            grouped_nested[k] = ', '.join(grouped_nested[k])
        except:
            continue

    obj[group_into_nested] = [grouped_nested]


# ---------------------


def path_from_mapping(mapping, column_name, logger=None):
    fieldname = util.get_json_value(mapping, column_name + '.name')
    if fieldname is None:
        return None, None, None

    fieldtype = util.get_json_value(mapping, column_name + '.type')

    path = util.get_json_value(mapping, column_name + '.path')
    if path is None:
        path = []

    if len(path) < 1:
        # simple field on top level of the object
        return None, fieldname, fieldtype

    # field is in path (nested tables and/or linked objects)
    _path = []
    for p in path:
        _p = util.get_json_value(p, 'name')
        _t = util.get_json_value(p, 'type')
        if not isinstance(_p, str):
            continue
        if _t != '_nested':
            continue
        _path.append('_nested:{}'.format(_p))

    return '.'.join(_path), fieldname, fieldtype
