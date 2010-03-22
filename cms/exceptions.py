class PluginAllreadyRegistered(Exception):
    pass

class AppAllreadyRegistered(Exception):
    pass

class NotImplemented(Exception):
    pass

class SubClassNeededError(Exception):
    pass

class MissingFormError(Exception):
    pass

class NoHomeFound(Exception):
    pass


class PermissionsException(Exception):
    """Base permission exception
    """

class NoPermissionsException(PermissionsException):
    """Can be fired when some violate action is performed on permission system. 
    """