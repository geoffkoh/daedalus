#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging

# Third party imports
import unittest

# Application imports
from daedalus.property.property import PropMap


logger = logging.getLogger(__name__)


class TestPropMap(unittest.TestCase):
    """ Test class for PropMap """


    def test_create_project(self):

        settings = {
            'rules': [
                {
                    'prop': {'class': 'general'},
                    'value': {'slots': 6}
                },
                {
                    'prop': {'class': 'cr'},
                    'value': {'slots': 12}
                },
                {
                    'prop': {'class': 'general', 'project': 'deepresearch'},
                    'value': {'slots': 10}
                },
                {
                    'prop': {'class': 'pm'},
                    'value': {'slots': 20}
                },

            ],
            
        }

        prop = PropMap(settings=settings)
        prop.generate2()
        print('')
        print(prop._data)

    # end test_create_project()

    def _create(self):
        """ Basic tests involving property map """

        settings = {
            'domain' : {
                'region': ['USA', 'EUR', 'ASI', 'JPN', 'XJP'],
                'delay': [0, 1],
                'intervalmode': ['1d', '5m', '15m', '60m'],
                'generator': ['HUMAN', 'RANDOM', 'AI'],
            },
            'range': {
                'tests': ['bias' 'checkpoint', 'memory', 'correlation']
            },
            'specifications': [
                {
                    'prop': {
                        'region': ['USA', 'EUR'],
                        'delay' : [1, 0],
                        'intervalmode': ['1d'],
                    },
                    'value': {
                        'tests': ['bias' 'checkpoint', 'memory', 'correlation']
                    },
                }, {
                    'prop': {
                        'region': ['USA', 'EUR'],
                        'delay': [0],
                        'intervalmode': ['5m', '15m', '60m'],
                    },
                    'value': {
                        'tests': ['bias', 'correlation'],
                    }
                }, {
                    'prop': {
                        'region': 'ASI',
                        'delay': [1, 0]
                    },
                    'value': {
                        'tests': ['bias']
                    },
                },
            ]
        }

        pm = PropMap(settings=settings)
        assert pm is not None
        pm.generate()
        # print(pm._data)

    # end test_create()

    def _sample_scale_factor(self):
        """ This test case tests with the submitquota scale factor as sample data """

        # Define the rules
        settings = {
            'rules' : [{
                'label': 'EUR_Base',
                'prop': {
                    'region': 'EUR',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.6,
                }
            }, {
                'label': 'MEA_Base',
                'prop': {
                    'region': 'MEA',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.1,
                }
            }, {
                'label': 'EAS_Base',
                'prop': {
                    'region': 'MEA',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.2,
                }
            }, {
                'label': 'GLOBAL_Base',
                'prop': {
                    'region': 'GLOBAL',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.5,
                }
            }, {
                'label': 'JPN_Base',
                'prop': {
                    'region': 'MEA',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.6,
                }
            }, {
                'label': 'ASI_Base',
                'prop': {
                    'region': 'ASI',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.4,
                }
            }, {
                'label': 'XJP_Base',
                'prop': {
                    'region': 'XJP',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.4,
                }
            }, {
                'label': 'CHN_Base',
                'prop': {
                    'region': 'CHN',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.1,
                }
            }, {
                'label': 'IND_Base',
                'prop': {
                    'region': 'IND',
                    'instruments': ['equity', 'vei'],
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.3,
                }
            }, {
                'label': 'CEF_Base',
                'prop': {
                    'instruments': 'cef',
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.3,
                }
            }, {
                'label': 'PFD_Base',
                'prop': {
                    'instruments': 'pfd',
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.1,
                }
            }, {
                'label': 'ETF_Base',
                'prop': {
                    'instruments': 'etf',
                    'intervalmode': '1d',
                    'generator': ['HUMAN', 'RANDOM', 'QUANTUM', 'AI']
                },
                'value': {
                    'scale_factor': 0.5,
                }
            }]
        }

        pm = PropMap(settings=settings)
        pm.generate()

        for row in pm._data.iterrows():
            print(row[0])

        # Tests getting some values
        value = pm.get({
            'instruments': 'equity',
            'intervalmode': '1d',
            'region': 'EUR'
        })
        print(value)

# end class TestPropMap
