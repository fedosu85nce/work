class ScriptBase(object):
    """
    Common interface to all scripts
    """

    def onPreInstall(self, data):
        """
        Handles the pre install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        raise NotImplementedError("Not implemented")
    # onPreInstall()

    def onPrepareInstall(self, data):
        """
        Handles the prepare install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        raise NotImplementedError("Not implemented")
    # onPrepareInstall()

    def onPostInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        raise NotImplementedError("Not implemented")
    # onPostInstall()

    def onPostUpgrade(self, data):
        """
        Handles the post upgrade event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        raise NotImplementedError("Not implemented")
    # onPostUpgrade()

# ScriptBase
