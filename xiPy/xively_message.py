# Copyright (c) 2003-2016, LogMeIn, Inc. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

class XivelyMessage:

    """XivelyMessage class is for encapsulating message parameters"""

    def __init__(self):

        """
        qos -- The QoS level of the QoS message, based on the MQTT specification.
        topic -- A string that represents the subscribed topic that was used to deliver the message to the
        Xively Client.
        payload -- A bytearray containing the payload of the incoming message.
        request_id -- The identifier of the publish request."""

        self.qos = 0
        self.topic = ""
        self.payload = None
        self.request_id = 0

    def __str__(self):

        return "topic: " + str( self.topic) + " payload: " + str( self.payload ) + " qos: " + str( self.qos ) + " request_id: " + str( self.request_id )
