# coding=utf8

import util
import zooniverse
import mapping

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


def api_zooniverse_import(easydb_context, parameters):
    logger = easydb_context.get_logger(PLUGIN_NAME)

    try:
        collected_objects, stats = zooniverse.parse_data(parameters['body'], logger)
        if not isinstance(collected_objects, dict):
            return util.json_error_response('could not parse body', logger)
        if collected_objects == {}:
            logger.warn('no zooniverse data was parsed from csv')
            return util.json_response(stats)

        columns_by_id = util.parse_datamodel(parameters['body'], logger)

        config = easydb_context.get_config()

        # load activated database languages from base config
        languages = util.get_json_value(config, 'base.system.languages.database')
        if not isinstance(languages, list) or len(languages) < 1:
            languages = ['de-DE']
        logger.debug('database languages: {}'.format(util.dumpjs(languages)))

        # load mappings from base config
        mappings = util.load_mappings(config, columns_by_id, logger)
        logger.debug('mappings: ' + util.dumpjs(mappings))

        stats['updated'] = {}
        stats['new'] = {}
        stats['count']['new'] = {}
        stats['count']['new_total'] = 0
        stats['count']['updated'] = {}
        stats['count']['updated_total'] = 0

        unique_linked_object_values = {}

        for objecttype in mappings:
            ot_mapping = mappings[objecttype]
            match_column = util.get_json_value(ot_mapping, 'match_column')
            if not isinstance(match_column, str):
                continue

            count_updated = 0

            # load objects with the collected signatures
            affected_objects = util.load_objects_by_signature(
                easydb_context,
                objecttype,
                match_column,
                list(collected_objects.keys()),
                logger
            )

            # iterate over objects, update objects with mapped data
            updated_objects = []
            for signatur in affected_objects:
                if signatur not in collected_objects:
                    logger.debug('signatur {0} not in collected objects -> skip'.format(signatur))
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
                            logger=logger,
                            signatur=signatur,
                            languages=languages
                        )
                        top_level_field_created = mapping.apply(
                            obj=obj,
                            unique_linked_object_values=unique_linked_object_values,
                            mapping=ot_mapping,
                            column_name='update_column_created_at',
                            value=created_at,
                            logger=logger,
                            signatur=signatur,
                            languages=languages
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
                                logger=logger,
                                signatur=signatur,
                                languages=languages
                            )

                version = util.get_json_value(obj, '_version')
                if not isinstance(version, int):
                    continue
                obj['_version'] = version + 1

                updated_objects.append(util.build_object(objecttype, obj))
                count_updated += 1

            stats['updated'][objecttype] = updated_objects
            stats['count']['updated'][objecttype] = count_updated
            stats['count']['updated_total'] += count_updated

        new_linked_objects, count_new = util.create_new_linked_objects(
            easydb_context,
            unique_linked_object_values,
            logger
        )
        stats['new'] = new_linked_objects
        stats['count']['new'] = count_new

        count_new_total = 0
        for ot in count_new:
            count_new_total += count_new[ot]
        stats['count']['new_total'] = count_new_total

        return util.json_response(stats, minify=True)

    except Exception as e:
        return util.json_error_response('could not parse zooniverse data: {0}'.format(e), logger)
