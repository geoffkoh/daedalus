#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test module for validating a JSON document where the JSON document
is a representation of the query for Alphahub API.
"""

# Standard imports
import sys
import logging

# Third party imports
from jsonschema import validate

logger = logging.getLogger(__name__)


class Validator:

    def __init__(self):
        """ Constructor """

        self._schema = Validator.default_schema()

    # end __init__()

    @staticmethod
    def default_schema():
        """ This is the default schema """
        schema = {

            '$schema': 'http://json-schema.org/draft-07/schema#',
            'description': 'The schema describing the Alphahub API query',

            # This part define some of the definitions that is
            # to be used.
            'definitions': {

                # Basic field names
                # that maps to entries in the tables
                'field': {
                    'oneOf': [{
                        'enum': [
                            'id',
                            'name',
                            'status',
                            'instruments',
                            'region',
                            'delay',
                            'birthday',
                            'intervalmode',
                            'prodsoftdate',
                            'prodstartdate',
                            # Some more, to be loaded from external file
                        ],
                    }],
                },

                # Operators
                'binary_operator': {
                    'oneOf': [{
                        'enum': [
                            '$eq',
                            '$ne',
                            '$gt',
                            '$ge',
                            '$lt',
                            '$le',
                        ]
                    }],
                },

                'ternary_operator': {
                    'oneOf': [{
                        'enum': [
                            '$between',
                        ],
                    }],
                },

                'membership_operator': {
                    'oneOf': [{
                        'enum': [
                            '$in',
                            '$nin',
                        ],
                    }],
                },

                # Basic value
                'value': {
                    'type': ['string', 'number']
                },

                'pair_value': {
                    'type': 'array',
                    'items': [
                        {'$ref': '#/definitions/value'},
                        {'$ref': '#/definitions/value'}
                    ],
                    "minItems": 2,
                    "maxItems": 2,
                },

                # List value
                'list_value': {
                    'type': 'array',
                    'items': {'$ref': '#/definitions/value'}
                },

                # binary_op_value
                'binary_op_value': {
                    'type': 'object',
                    'propertyNames': {
                        '$ref': '#/definitions/binary_operator',
                    },
                    'patternProperties': {
                        '': {
                            '$ref': '#/definitions/value',
                        }
                    },
                },

                # ternary_op_value
                'ternary_op_value': {
                    'type': 'object',
                    'propertyNames': {
                        '$ref': '#/definitions/ternary_operator',
                    },
                    'patternProperties': {
                        '': {
                            '$ref': '#/definitions/pair_value',
                        },
                    },
                },

                # membership_op_value
                'membership_op_value': {
                    'type': 'object',
                    'propertyNames': {
                        '$ref': '#/definitions/membership_operator',
                    },
                    'patternProperties': {
                        '': {
                            '$ref': '#/definitions/list_value',
                        },
                    },
                },

                # Basic field-value condition
                'field_condition': {
                    'type': 'object',
                    'propertyNames': {
                        '$ref': '#/definitions/field',
                    },
                    'patternProperties': {
                        '': {
                            'anyOf': [
                                {'$ref': '#/definitions/value'},
                                {'$ref': '#/definitions/list_value'},
                                {'$ref': '#/definitions/binary_op_value'},
                                {'$ref': '#/definitions/ternary_op_value'},
                                {'$ref': '#/definitions/membership_op_value'},
                            ],
                        }
                    },
                },

                # Binary comparison condition
                'binary_comp_condition': {
                    'type': 'object',
                    'propertyNames': {
                        '$ref': '#/definitions/binary_operator',
                    },
                    'patternProperties': {
                        '': {
                            'type': 'array',
                            'items': [
                                {'$ref': '#/definitions/field'},
                                {'$ref': '#/definitions/value'}
                            ],
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                },

                # Ternary comparison condition
                'ternary_comp_condition': {
                    'type': 'object',
                    'propertyNames': {
                        '$ref': '#/definitions/ternary_operator',
                    },
                    'patternProperties': {
                        '': {
                            'type': 'array',
                            'items': [
                                {'$ref': '#/definitions/field'},
                                {'$ref': '#/definitions/value'},
                                {'$ref': '#/definitions/value'},
                            ],
                            "minItems": 3,
                            "maxItems": 3,
                        },
                    },
                },


            },

            # The actual query object
            'type': 'object',
            'properties': {
                'filter': {'oneOf': [
                    {
                        'type': 'array',
                        'items': {
                            'oneOf': [
                                {'$ref': '#/definitions/field_condition'},
                                {'$ref': '#/definitions/binary_comp_condition'},
                                {'$ref': '#/definitions/ternary_comp_condition'},
                            ],
                        },
                    },
                    {
                        '$ref': '#/definitions/field_condition',
                    }
                ]},

                # ====
                # This is not yet finished. Just the filter portion
                # ====
            },
        }
        return schema
    # end default_schema()

    def validate(self, query: dict):
        """ Validates the query using the schema """

        return validate(instance=query, schema=self._schema)

    # end validate()


if __name__ == '__main__':

    print('This is just for testing of validation codes')
    validator = Validator()

    test_query = {
        'filter': {
            'status': 'PROD',
            'instruments': 'equity',
            'region': 'USA',
            'delay': 1,
            'birthday': ['2019-11-20', '2019-11-21'],
            'intervalmode': {
                '$gt': '1',
            },
            'prodsoftdate': {
                '$between': ['2019-11-12', '2019-11-22'],
            },
            'prodstartdate': {
                '$between': ['2019-11-12', '2019-11-22'],
            },
        },
    }
    validator.validate(test_query)
