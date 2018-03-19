# Copyright (c) 2003-2016, Xively. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

class XivelyErrorCodes:

    """Possible error codes passed to the user by XivelyClient"""
    XI_STATE_OK = 0
    XI_STATE_TIMEOUT = 1
    XI_BACKOFF_TERMINAL = 2
    XI_CONNECTION_RESET_BY_PEER_ERROR = 3
    XI_TLS_CONNECT_ERROR = 4
    XI_TLS_CERTIFICATE_ERROR = 5
    XI_MQTT_SERVER_UNAVAILIBLE = 6
    XI_MQTT_BAD_USERNAME_OR_PASSWORD = 7
    XI_MQTT_CONNECT_UNKNOWN_RETURN_CODE = 8
    XI_MQTT_NOT_AUTHORIZED = 9
    XI_MQTT_UNACCEPTABLE_PROTOCOL_VERSION = 10
    XI_MQTT_IDENTIFIER_REJECTED = 11
    XI_SOCKET_ERROR = 12
    XI_SOCKET_CONNECTION_ERROR = 13
