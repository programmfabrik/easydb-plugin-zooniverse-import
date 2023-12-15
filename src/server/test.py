# coding=utf8

import unittest
import json
from datetime import datetime

import util
import mapping


class Logger(object):

    __COL_BLUE = '\033[94m'
    __COL_CYAN = '\033[96m'
    __COL_GREEN = '\033[92m'
    __COL_YELLOW = '\033[93m'
    __COL_RED = '\033[91m'
    __BOLD = '\033[1m'
    __UNDERLINE = '\033[4m'
    __ENDC = '\033[0m'

    @classmethod
    def color(cls, msg, color):
        return color + str(msg) + cls.__ENDC

    @classmethod
    def bold(cls, msg):
        return cls.__BOLD + str(msg) + cls.__ENDC

    @classmethod
    def underline(cls, msg):
        return cls.__UNDERLINE + str(msg) + cls.__ENDC

    @classmethod
    def red(cls, msg):
        return cls.color(msg, color=cls.__COL_RED)

    @classmethod
    def blue(cls, msg):
        return cls.color(msg, color=cls.__COL_BLUE)

    @classmethod
    def cyan(cls, msg):
        return cls.color(msg, color=cls.__COL_CYAN)

    @classmethod
    def yellow(cls, msg):
        return cls.color(msg, color=cls.__COL_YELLOW)

    @classmethod
    def green(cls, msg):
        return cls.color(msg, color=cls.__COL_GREEN)

    # --------------------------------------------------------------------

    @classmethod
    def dump_json(cls, js, indent=4):
        return json.dumps(js, indent=indent)

    # --------------------------------------------------------------------

    def __init__(self, name=None) -> None:
        self.name = name
        pass

    def __format_string_list(self, strings):
        string_list = []
        for s in strings:
            if isinstance(s, str):
                string_list.append(s)
            else:
                string_list.append(str(s))

        return ' '.join(string_list)

    def __prefix(self, p):
        now = datetime.utcnow()
        if self.name is None:
            return '[{0}] [{1}] '.format(now, p)
        n = 16
        return '[{0}] [{1}] [{2}{3}] '.format(
            now, p,
            ' ' * (n - len(self.name)),
            self.name[-n:]
        )

    def info(self, *strings):
        print(self.__prefix(self.blue(' INFO')) + self.__format_string_list(strings))

    def debug(self, *strings):
        print(self.__prefix(self.cyan('DEBUG')) + self.__format_string_list(strings))

    def warn(self, *strings):
        print(self.__prefix(self.yellow(' WARN')) + self.__format_string_list(strings))

    def error(self, *strings):
        print(self.__prefix(self.red('ERROR')) + self.__format_string_list(strings))


class mapping__apply(unittest.TestCase):

    def test(self):
        self.maxDiff = None

        logger = Logger('mapping__apply')
        print()

        for c in [
            ('{}', None, {}, {}),
            ('null', None, {}, {}),
            ('{}', 'xxx', {}, {}),
            ('null', 'xxx', {}, {}),
            ("""
                {
                    "xxx": {
                        "name": "schlagwort",
                        "type": "text_oneline"
                    }
                }
            """, None, {}, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "type": "text_oneline"
                    }
                }
            """, None, {}, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_1', {
                'schlagwort': 'test_value_1'
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "datum",
                        "type": "datetime"
                    }
                }
            """, '2022-10-12T08:49:36+2:00', {
                'datum': {
                    'value': '2022-10-12T08:49:36+2:00'
                }
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "type": "text_l10n"
                    }
                }
            """, 'test_value_1__l10n', {
                'schlagwort': {
                    'de-DE': 'test_value_1__l10n',
                    'en-US': 'test_value_1__l10n',
                }
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "schlagwort",
                                "type": "link"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'xxx', {}, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "schlagwort",
                                "objecttype": "keywords",
                                "type": "link"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_2', {
                'schlagwort': {
                    '_mask': '_all_fields',
                    '_objecttype': 'keywords',
                    'keywords': {
                        'lookup:_id': {
                            'schlagwort': 'test_value_2'
                        }
                    }
                }
            }, {
                'keywords': {
                    'schlagwort': ['test_value_2']
                }
            }),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_3', {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': 'test_value_3'
                    }
                ]
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_l10n"
                    }
                }
            """, 'test_value_3__l10n', {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': {
                            'de-DE': 'test_value_3__l10n',
                            'en-US': 'test_value_3__l10n',
                        }
                    }
                ]
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "datum",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "datetime"
                    }
                }
            """, '2022-10-12T08:49:36+2:00', {
                '_nested:assets__schlagwoerter': [
                    {
                        'datum': {
                            'value': '2022-10-12T08:49:36+2:00',
                        }
                    }
                ]
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            },
                            {
                                "name": "assets__schlagwoerter__sub",
                                "type": "_nested"
                            },
                            {
                                "name": "assets__schlagwoerter__sub__sub",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_4', {
                '_nested:assets__schlagwoerter': [
                    {
                        '_nested:assets__schlagwoerter__sub': [
                            {
                                '_nested:assets__schlagwoerter__sub__sub': [
                                    {
                                        'schlagwort': 'test_value_4'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            },
                            {
                                "name": "schlagwort",
                                "objecttype": "keywords",
                                "type": "link"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_5', {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': {
                            '_mask': '_all_fields',
                            '_objecttype': 'keywords',
                            'keywords': {
                                'lookup:_id': {
                                    'schlagwort': 'test_value_5'
                                }
                            }
                        }
                    }
                ]
            }, {
                'keywords': {
                    'schlagwort': ['test_value_5']
                }
            }),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            },
                            {
                                "name": "assets__schlagwoerter__sub",
                                "type": "_nested"
                            },
                            {
                                "name": "schlagwort",
                                "objecttype": "keywords",
                                "type": "link"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_6', {
                '_nested:assets__schlagwoerter': [
                    {
                        '_nested:assets__schlagwoerter__sub': [
                            {
                                'schlagwort': {
                                    '_mask': '_all_fields',
                                    '_objecttype': 'keywords',
                                    'keywords': {
                                        'lookup:_id': {
                                            'schlagwort': 'test_value_6'
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }, {
                'keywords': {
                    'schlagwort': ['test_value_6']
                }
            }),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, [
                'test_value_7__01',
                'test_value_7__02',
                'test_value_7__03',
                'test_value_7__04',
                'test_value_7__03'
            ], {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': 'test_value_7__01'
                    },
                    {
                        'schlagwort': 'test_value_7__02'
                    },
                    {
                        'schlagwort': 'test_value_7__03'
                    },
                    {
                        'schlagwort': 'test_value_7__04'
                    }
                ]
            }, {}),
            ("""
                {
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            },
                            {
                                "name": "schlagwort",
                                "objecttype": "keywords",
                                "type": "link"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, [
                'test_value_8__01',
                'test_value_8__02',
                'test_value_8__03',
                'test_value_8__04',
                'test_value_8__03'
            ], {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': {
                            '_mask': '_all_fields',
                            '_objecttype': 'keywords',
                            'keywords': {
                                'lookup:_id': {
                                    'schlagwort': 'test_value_8__01'
                                }
                            }
                        }
                    },
                    {
                        'schlagwort': {
                            '_mask': '_all_fields',
                            '_objecttype': 'keywords',
                            'keywords': {
                                'lookup:_id': {
                                    'schlagwort': 'test_value_8__02'
                                }
                            }
                        }
                    },
                    {
                        'schlagwort': {
                            '_mask': '_all_fields',
                            '_objecttype': 'keywords',
                            'keywords': {
                                'lookup:_id': {
                                    'schlagwort': 'test_value_8__03'
                                }
                            }
                        }
                    },
                    {
                        'schlagwort': {
                            '_mask': '_all_fields',
                            '_objecttype': 'keywords',
                            'keywords': {
                                'lookup:_id': {
                                    'schlagwort': 'test_value_8__04'
                                }
                            }
                        }
                    }
                ]
            }, {
                'keywords': {
                    'schlagwort': [
                        'test_value_8__01',
                        'test_value_8__02',
                        'test_value_8__03',
                        'test_value_8__04',
                    ]
                }
            }),
            ("""
                {
                    "split_test_column_name": false,
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_9__01; test_value_9__02,test_value_9__03', {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': 'test_value_9__01; test_value_9__02,test_value_9__03'
                    }
                ]
            }, {}),
            ("""
                {
                    "split_test_column_name": true,
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_10__01; test_value_10__02,test_value_10__03', {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': 'test_value_10__01'
                    },
                    {
                        'schlagwort': 'test_value_10__02'
                    },
                    {
                        'schlagwort': 'test_value_10__03'
                    }
                ]
            }, {}),
            ("""
                {
                    "split_test_column_name": true,
                    "test_column_name": {
                        "name": "schlagwort",
                        "path": [
                            {
                                "name": "assets__schlagwoerter",
                                "type": "_nested"
                            }
                        ],
                        "type": "text_oneline"
                    }
                }
            """, 'Tourismus, Sehenswürdigkeit, Elbufer', {
                '_nested:assets__schlagwoerter': [
                    {
                        'schlagwort': 'Tourismus'
                    },
                    {
                        'schlagwort': 'Sehenswürdigkeit'
                    },
                    {
                        'schlagwort': 'Elbufer'
                    }
                ]
            }, {}),
            ("""
                {
                    "split_test_column_name": true,
                    "test_column_name": {
                        "name": "schlagwort",
                        "type": "text_oneline"
                    }
                }
            """, 'test_value_10__01; test_value_10__02,test_value_10__03', {
                'schlagwort': 'test_value_10__01; test_value_10__02,test_value_10__03'
            }, {}),
        ]:
            input_mapping = json.loads(c[0])
            input_value = c[1]
            expected_object = c[2]
            expected_linked_objects = c[3]

            result_object = {}
            result_linked_objects = {}

            logger.debug(Logger.green('input mapping:'), Logger.dump_json(input_mapping))
            logger.debug('expected:', Logger.dump_json(expected_object))

            mapping.apply(
                obj=result_object,
                unique_linked_object_values=result_linked_objects,
                mapping=input_mapping,
                column_name='test_column_name',
                value=input_value,
                signatur='test_signatur',
                languages=['de-DE', 'en-US'],
                logger=logger,
            )

            logger.debug('result:', Logger.dump_json(result_object))
            logger.debug('expected linked objects:', Logger.dump_json(expected_linked_objects))
            logger.debug('result:', Logger.dump_json(result_linked_objects))

            self.assertDictEqual(result_object, expected_object, msg=logger.red('expected_object'))
            self.assertDictEqual(result_linked_objects, expected_linked_objects, msg=logger.red('expected_linked_objects'))


class util__format_date(unittest.TestCase):

    def test(self):
        logger = Logger('util__format_date')
        print()

        for c in [
            (None, None),
            ('', None),
            ('xxx', None),
            ('2022', {'value': '2022'}),
            ('2022-10', {'value': '2022-10'}),
            ('2022-10-12', {'value': '2022-10-12'}),
            ('2022-10-12T08', {'value': '2022-10-12'}),
            ('2022-10-12T08:49', {'value': '2022-10-12'}),
            ('2022-10-12T08:49:36', {'value': '2022-10-12'}),
            ('2022-10-12T08:49:36+2:00', {'value': '2022-10-12'}),
            ('2022-10-12T08:27:55+0:00', {'value': '2022-10-12'}),
            ('2022-10-12T08:49:36-2:00', {'value': '2022-10-12'}),
            ('2022-10-12 08', {'value': '2022-10-12'}),
            ('2022-10-12 08:49', {'value': '2022-10-12'}),
            ('2022-10-12 08:49:36', {'value': '2022-10-12'}),
            ('2022-10-12 08:49:36+2:00', {'value': '2022-10-12'}),
            ('2022-10-12 08:27:55+0:00', {'value': '2022-10-12'}),
            ('2022-10-12 08:49:36-2:00', {'value': '2022-10-12'}),
        ]:
            logger.info(c[0], '=>', str(c[1]))
            if not isinstance(c[1], dict):
                self.assertEqual(util.format_date(c[0]), c[1])
                continue
            self.assertDictEqual(util.format_date(c[0]), c[1])


class util__format_datetime(unittest.TestCase):

    def test(self):
        logger = Logger('util__format_datetime')
        print()

        for c in [
            (None, None),
            ('', None),
            ('xxx', None),
            ('2022', {'value': '2022'}),
            ('2022-10', {'value': '2022-10'}),
            ('2022-10-12', {'value': '2022-10-12'}),
            ('2022-10-12T08', {'value': '2022-10-12T08'}),
            ('2022-10-12T08:49', {'value': '2022-10-12T08:49'}),
            ('2022-10-12T08:49:36', {'value': '2022-10-12T08:49:36'}),
            ('2022-10-12T08:49:36+2:00', {'value': '2022-10-12T08:49:36+2:00'}),
            ('2022-10-12T08:27:55+0:00', {'value': '2022-10-12T08:27:55+0:00'}),
            ('2022-10-12T08:49:36-2:00', {'value': '2022-10-12T08:49:36-2:00'}),
            ('2022-10-12 08', {'value': '2022-10-12 08'}),
            ('2022-10-12 08:49', {'value': '2022-10-12 08:49'}),
            ('2022-10-12 08:49:36', {'value': '2022-10-12 08:49:36'}),
            ('2022-10-12 08:49:36+2:00', {'value': '2022-10-12 08:49:36+2:00'}),
            ('2022-10-12 08:27:55+0:00', {'value': '2022-10-12 08:27:55+0:00'}),
            ('2022-10-12 08:49:36-2:00', {'value': '2022-10-12 08:49:36-2:00'}),
        ]:
            logger.info(c[0], '=>', str(c[1]))
            if not isinstance(c[1], dict):
                self.assertEqual(util.format_datetime(c[0]), c[1])
                continue
            self.assertDictEqual(util.format_datetime(c[0]), c[1])


class util__split_value(unittest.TestCase):

    def test(self):
        logger = Logger('util__split_value')
        print()

        for c in [
            (None, None),
            ('', None),
            ('a', ['a']),
            (['a'], ['a']),
            (['a', 'b'], ['a', 'b']),
            ('a,b', ['a', 'b']),
            (',a,b,', ['a', 'b']),
            (',a,;b,', ['a', 'b']),
            ('a;b', ['a', 'b']),
            ('a,b;', ['a', 'b']),
            (['a,b;', 'c', 'd;e'], ['a', 'b', 'c', 'd', 'e']),
            (['Tourismus, Sehenswürdigkeit, Elbufer'], ['Tourismus', 'Sehenswürdigkeit', 'Elbufer']),
            (['Tourismus, Sehensw\u00fcrdigkeit, Elbufer'], ['Tourismus', 'Sehensw\u00fcrdigkeit', 'Elbufer']),
        ]:
            logger.info(c[0], '=>', str(c[1]))
            if not isinstance(c[1], list):
                self.assertEqual(util.split_value(c[0]), c[1])
                continue
            self.assertListEqual(util.split_value(c[0]), c[1])


if __name__ == '__main__':
    unittest.main()
