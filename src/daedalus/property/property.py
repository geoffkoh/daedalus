#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for handling properties and the values they map to.

The basic premise of a ``PropMap`` is that it maps a set of properties (domain) to a set of values (range).
This has several uses including a standard way to codify rules and properties, such as the set
of tests that are valid for a certain classes of Alphas, or a set of simulation limits that
are available for different types of Metas.

One of the uses of a property map is conflict resolution policies, i.e. if we find that for the set
of rules in the property map that matches the given properties, which one do we select.

It should also allow us to reverse the map, i.e given the set of mapping values, tell us what
are the properties that would make it possible.

Here are some requirements on the specification of a property map:

* Each specification could have a label/name to it
* The property domain and range values can either be pre-specified, or generated on the spot

A sample of how a property map is specified can be represented by the snippet below:

.. code-block:: python

    # Optional
    domain: {
        region: ['USA', 'ASI', 'EUR'],
        interval: [1, 0],
    },

    # Optional
    range: {
        tests: ['checkBias', 'checkBase'],
        scale_factor: None  # None to indicate no bound
    },

    # Default value if no match
    default: {
        tests: ['checkBias', 'checkBase'],
    },

    # Optional policies
    'match': <'first'|'last'|'all'>,
    'build': <'ignore'|'overwrite'|'append'|'strict'>,
    'filter': <'equal'|'subset'>

    rules: [
        {
            name: 'rule_1',
            prop: {
                region: ['USA', 'ASI']
            },
            value: {
                tests: ['bias']
            }
        }
    ]


Sample usage
============

Here is some sample usage

.. code-block:: python

    pmap = PropertyMap(settings)


"""

# System imports
import itertools
import copy
import logging

# Third party imports
import pandas as pd
import numpy as np

# Application imports

logger = logging.getLogger(__name__)


class PropMapError(Exception):
    """ Default error class for any exception """
# end class PropertyMapError


class PropMap:
    """ This is the class that will take in a set of
    properties and map them to a set of values.

    The role played by ``PropMap`` essentially is the definition of functions
    in set theory. The domain is the list of properties and their allowable values,
    and the values
    """

    _match_policy = {
        'first': lambda x: x[0],
        'last': lambda x: x[-1],
    }

    def __init__(self, settings: dict = None) -> 'PropMap':
        """ Constructor """

        settings = settings or {}

        self._domain = settings.get('domain', None)
        self._range = settings.get('range', None)
        self._rules = settings.get('rules', [])
        self._default = settings.get('default', None)

        # Extract out the other parameters
        self._match = settings.get('match', 'first')
        self._build = settings.get('build', 'override')
        self._filter = settings.get('filter', 'equal')

        # Sets the data to None first
        self._data = None

    # end __init__()

    def add_rule(self, prop_map: dict, value_map: dict, label: str=None):
        """ Adds a rule to the property map """

        rule = {
            'property': prop_map,
            'value': value_map,
            'label': label,
        }
        self._rules.append(rule)

    # end add_rule()

    def _get_columns(self):
        """ Get the column names based on the existing domain and range maps. """

        columns = list(self._domain.keys())
        columns.extend(self._range.keys())
        return columns

    # end _get_columns()

    def _collect(self):
        """ Collects the property domain and value range from the rules """

        prop_domain = {}
        prop_range = {}

        for rule in self._rules:
            prop = rule.get('prop', {})
            value = rule.get('value', {})

            # Adds in for the domain
            for prop_key, prop_value in prop.items():
                prop_value = prop_value if type(prop_value) is list else [prop_value,]
                if prop_key in prop_domain:
                    prop_domain[prop_key].extend(prop_value)
                else:
                    prop_domain[prop_key] = prop_value

            # Adds in for the range
            for range_key, range_value in value.items():
                range_value = range_value if type(range_value) is list else [range_value,]
                if range_key in prop_range:
                    prop_range[range_key].extend(range_value)
                else:
                    prop_range[range_key] = range_value

        # Remove duplicates
        self._domain = {key: list(set(value)) for key, value in prop_domain.items()}
        self._range = {key: list(set(value)) for key, value in prop_range.items()}

    # end _collect()

    def map(self, prop_map: dict = None) -> pd.DataFrame:
        """ Maps a dictionary of parameters to the set of values """

        # Creates a copy of the property query and convert all values into list
        prop_map = copy.deepcopy(prop_map)

        filter_series = pd.Series(np.ones(self._data.shape[0], dtype=bool))
        for key, value in prop_map.items():
            if type(value) != list:
                filter_series = ((self._data[key] == value) & filter_series)
            else:
                filter_series = ((self._data[key].isin(value)) & filter_series)

        # Filters the dataframe using the modified prop
        result = self._data[filter_series]
        return result

    # end map()

    def get(self, prop_map: dict) -> dict:
        """ Gets a single entry given the prop_map.

        If the property map maps to more than one possibilty, it will pick
        according to the selection policy, i.e. first, last
        """

        result_df = self.map(prop_map)
        if len(result_df) == 0:
            return None

        result_maplist = self._dataframe_to_dict(result_df, self._range.keys())
        matched = self._match_policy[self._match](result_maplist)
        return matched

    # end get()

    def _dataframe_to_dict(self, data: pd.DataFrame, columns: list = None):
        """ Extracts out the data into a list of dictionary """

        value_list = data.to_dict('records')
        if columns:
            value_list = [dict({k:value[k] for k in columns if k in value}) for value in value_list]
        return value_list

    # end _dataframe_to_dict()

    def generate(self) -> bool:
        """ Based on the existing rules, re-generates the data

        This method will get the cartesian product of all the domain values
        and populates the internal dataframe with it.

        It then runs through the rules such that for each entry that satisfy the
        domain component, the value component will be populated with the list of values
        """

        # If the domain and range are None, we try to build
        # using the existing rules
        if self._domain is None and self._range is None:
            self._collect()

        # Prepares the column headers
        columns = self._get_columns()

        # creates a new dataframe
        data = []
        keys = list(self._domain.keys())
        for entry in itertools.product(*self._domain.values()):
            combination = dict(zip(keys, list(entry)))
            data.append(combination)
        self._data = pd.DataFrame(data, columns=columns, dtype=object)

        # Goes through the specifications and assigns them with values
        for rule in self._rules:

            # Gets the values off the rules
            prop_map = rule.get('prop', {})
            value_map = rule.get('value', {})
            name = rule.get('name', None)

            # Filter out the data first
            filtered_data = self.map(prop_map)

            # Updates the result with the values
            for index, row in filtered_data.iterrows():
                for key, value in value_map.items():
                    self._data.at[index, key] = value

        # Drops the combinations that does not have values
        self._data.dropna()

        return True

    # end generate()

    @staticmethod
    def _conflict_policy_override(data, index, value_map, name):
        for key, value in value_map.items():
            data.at[index, key] = value

    @staticmethod
    def _conflict_policy_ignore(data, row, value_map, name):
        pass

    @staticmethod
    def _conflict_policy_append(data, row, value_map, name):
        pass


# end class PropertyMap

