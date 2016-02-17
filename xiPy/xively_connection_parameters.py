# Copyright (c) 2003-2016, LogMeIn, Inc. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

class XivelyConnectionParameters:

    """XivelyClient Connection parameters"""

    def __init__(self):

        self.username = None
        self.password = None

        self.client_id = None
        self.keep_alive = 60
        self.clean_session = False
        self.connection_timeout = 10

        self.will_qos = 0
        self.will_topic = None
        self.will_retain = False
        self.will_message = None

        self.use_websocket = False
