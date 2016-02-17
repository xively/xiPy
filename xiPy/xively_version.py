# Copyright (c) 2003-2016, LogMeIn, Inc. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

class XivelyClientVersion:
    major = 0
    minor = 7
    revision = 0

    @staticmethod
    def get_version_string():
        return str(XivelyClientVersion.major) \
        + "." + str(XivelyClientVersion.minor) \
        + "." + str(XivelyClientVersion.revision)
