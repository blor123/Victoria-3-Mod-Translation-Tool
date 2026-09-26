class V3MMError(Exception):
    """Base error that is safe to summarize in the GUI."""


class InputValidationError(V3MMError):
    pass


class ArchiveValidationError(V3MMError):
    pass


class DuplicateTargetError(V3MMError):
    pass


class OperationCancelled(V3MMError):
    pass
