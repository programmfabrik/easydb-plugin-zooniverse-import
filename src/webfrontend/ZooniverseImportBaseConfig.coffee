class ZooniverseImportBaseConfig extends BaseConfigPlugin
    getFieldDefFromParm: (baseConfig, fieldName, def) ->

        @key_prefix = "server.config.parameter.system.zooniverse_import.mappings."
        @key_label_suffix = ".label"
        @key_hint_suffix = ".label|hint"

        sort = (a, b) ->
            return a.text.localeCompare(b.text)

        getMask = (idTable) ->
            if CUI.util.isString(idTable)
                return false
            return Mask.getMaskByMaskName("_all_fields", idTable)

        __isObjectField = (field, data, parentField) ->
            return not field.isTopLevelField() and not field.isSystemField() and
                field.__csl not in [
                    "ez5-pool-field",
                    "ez5-version-column"
                ]

        filterTextField = (field, data, parentField) ->
            return __isObjectField(field, data, parentField) and field instanceof TextColumn

        filterTextFieldInNested = (field, data, parentField) ->
            return __isObjectField(field, data, parentField) and field.insideNested() and field instanceof TextColumn

        filterTextLinkField = (field, data, parentField) ->
            return __isObjectField(field, data, parentField) and
                (field instanceof TextColumn or field instanceof LocaTextColumn)

        filterDateField = (field, data, parentField) ->
            return __isObjectField(field, data, parentField) and field instanceof DateTimeColumn

        filterDateFieldInNested = (field, data, parentField) ->
            return __isObjectField(field, data, parentField) and field.insideNested() and
                (field instanceof DateTimeColumn or field instanceof DateColumn)


        if def.plugin_type == "update_objecttype"
            field = new ez5.ObjecttypeSelector
                form:
                    label: $$(@key_prefix + def.plugin_type + @key_label_suffix)
                    hint:  $$(@key_prefix + def.plugin_type + @key_hint_suffix)
                name: fieldName
                show_name: true
                store_value: "fullname"
                sort: sort
                filter: (objecttype) ->
                    mask = getMask(objecttype.table.id())
                    if not mask
                        return false

                    objecttype.addMask(mask)

                    hasTextField = objecttype.getFields().some((field, data, parentField) -> field instanceof TextColumn)

                    return hasTextField
            return field

        if def.plugin_type == "match_column"
            field = new ez5.FieldSelector
                form:
                    label: $$(@key_prefix + def.plugin_type + @key_label_suffix)
                    hint:  $$(@key_prefix + def.plugin_type + @key_hint_suffix)
                name: fieldName
                objecttype_data_key: "update_objecttype"
                store_value: "fullname"
                sort: sort
                show_name: true
                filter: filterTextField
            return field


        if def.plugin_type == "update_column_user_name"
            field = new ez5.FieldSelector
                form:
                    label: $$(@key_prefix + def.plugin_type + @key_label_suffix)
                    hint:  $$(@key_prefix + def.plugin_type + @key_hint_suffix)
                name: fieldName
                objecttype_data_key: "update_objecttype"
                store_value: "id"
                deep_linked_objects: true
                sort: sort
                show_name: true
                filter: filterTextFieldInNested
            return field

        if def.plugin_type == "update_column_created_at"
            field = new ez5.FieldSelector
                form:
                    label: $$(@key_prefix + def.plugin_type + @key_label_suffix)
                    hint:  $$(@key_prefix + def.plugin_type + @key_hint_suffix)
                name: fieldName
                objecttype_data_key: "update_objecttype"
                store_value: "id"
                deep_linked_objects: true
                sort: sort
                show_name: true
                filter: filterDateFieldInNested
            return field

        if def.plugin_type.startsWith("update_column_")
            field = new ez5.FieldSelector
                form:
                    label: $$(@key_prefix + def.plugin_type + @key_label_suffix)
                    hint:  $$(@key_prefix + def.plugin_type + @key_hint_suffix)
                name: fieldName
                objecttype_data_key: "update_objecttype"
                store_value: "id"
                deep_linked_objects: true
                sort: sort
                show_name: true
                filter: filterTextLinkField
            return field


ez5.session_ready =>
    BaseConfig.registerPlugin(new ZooniverseImportBaseConfig())