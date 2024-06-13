
class CTDException(Exception):
    pass


class MissingAttribute(CTDException):
    pass


class UnrecognizedFileName(CTDException):
    pass


class InvalidInstrumentName(CTDException):
    pass


class InvalidInstrumentSerialNumber(CTDException):
    pass


class InvalidDateFormat(CTDException):
    pass


class InvalidTimeFormat(CTDException):
    pass


class InvalidCountryCode(CTDException):
    pass


class InvalidSerialNumber(CTDException):
    pass


class InvalidFileNameFormat(CTDException):
    pass


class PathError(CTDException):
    pass


class InvalidSurfacesoak(CTDException):
    pass


class InvalidParameterIndex(CTDException):
    pass


class FileExists(CTDException):
    pass

