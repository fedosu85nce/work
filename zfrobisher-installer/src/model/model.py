#
# IMPORTS
#
import logging

#
# CODE
#
class Model(object):
    """
    Abstracts a data model for KoP installer
    """

    def __init__(self):
        """
        Creates a model object

        @rtype:   nothing
        @returns: nothing
        """
        self.__logger = logging.getLogger(__name__)
        self.__data = {}

    # __init__()

    def insert(self, key, value):
        """
        Inserts a new entry in the model

        @type  key: str
        @param key: key of the value to be inserted

        @type  value: arbitrary
        @param value: value to be inserted

        @rtype:   nothing
        @returns: nothing
        """
        try:
            # key must be string by contract
            assert isinstance(key, str)

            # store the data
            self.__data[key] = value
        except Exception as e:
            self.__logger.critical("%s" % e)
    # insert()

    def get(self, key):
        """
        Retrieved data from model
        The caller is responsible to handle a non existing key

        @type  key: str
        @param key: key of the value to be get

        @rtype:   arbitrary
        @returns: value
        """
        try:
            # key must be string by contract
            assert isinstance(key, str)

            result = None
            if self.__data.has_key(key):
                result = self.__data[key]

            # return the data
            return result
        except Exception as e:
            self.__logger.critical("%s" % e)

    # get()

# Model
