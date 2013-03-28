# -*- coding: utf-8 -*-
class PluginAlreadyRegistered(Exception):
    pass


class PluginNotRegistered(Exception):
    pass


class AppAlreadyRegistered(Exception):
    pass

AppAllreadyRegistered = AppAlreadyRegistered # backwards compatibility, will be dropped in 2.3

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

class PublicIsUnmodifiable(Exception):
    """A method was invoked on the public copy, but is only valid for the
    draft version"""
    pass

class Deprecated(Exception): pass


class DuplicatePlaceholderWarning(Warning): pass


class DontUsePageAttributeWarning(Warning): pass


class CMSDeprecationWarning(Warning): pass


class LanguageError(Exception): pass