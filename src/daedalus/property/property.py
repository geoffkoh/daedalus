#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for handling rules and property.

The basic premise of a property map is that it maps a set of properties to a set of values.
This has several uses including a standard way to codify rules and properties, such as the set
of tests that are valid for a certain classes of Alphas, or a set of simulation limits that
are available for different types of Metas.

One of the uses of a property map is conflict resolution policies, i.e. if we find that for the set
of rules in the property map that matches the given properties, which one do we select.

It should also allow us to reverse the map, i.e given the set of mapping values, tell us what
are the properties that would make it possible.

The specification of a property map is as such:




"""

# System imports
import logging

# Third party imports

# Application imports

logger = logging.getLogger(__name__)


class PropertyMap:
    """ This is the class that will take in a set of
    properties and map them to a set of values """

    def __init__(self):
        """ Constructor """
        pass
    # end __init__()

    def map(self, property_map: dict = None) -> dict:
        """ Maps a dictionary of parameters to the set of values """

        property_map = property_map or {}

        return property_map

    # end map()

# end class PropertyMap

if __name__ == '__main__':

    print('This is a test')