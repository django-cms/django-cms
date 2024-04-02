class PluginAlreadyRegistered(Exception):
    pass


class PluginNotRegistered(Exception):
    pass


class PluginLimitReached(Exception):
    """Gets triggered when a placeholder has reached its plugin limit."""

    pass


class AppAlreadyRegistered(Exception):
    pass


class ToolbarAlreadyRegistered(Exception):
    pass


class ToolbarNotRegistered(Exception):
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
    """Base permission exception"""


class NoPermissionsException(PermissionsException):
    """Can be fired when some violate action is performed on permission system."""


class PublicIsUnmodifiable(Exception):
    """A method was invoked on the public copy, but is only valid for the
    draft version"""

    pass


class PublicVersionNeeded(Exception):
    """A Public version of this page is needed"""

    pass


class Deprecated(Exception):
    pass


class DuplicatePlaceholderWarning(Warning):
    pass


class DontUsePageAttributeWarning(Warning):
    pass


class LanguageError(Exception):
    pass


class PluginConsistencyError(Exception):
    pass


class PlaceholderNotFound(Exception):
    pass


class ConfirmationOfVersion4Required(Exception):
    pass
