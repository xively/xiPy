# Copyright (c) 2003-2016, Xively. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

import os
import sys
import ssl
import struct
import time
import threading
from socket import error as socketerror
from . import paho_mqtt_client
from .xively_callback_handler import XivelyCallbackHandler
from .paho_mqtt_client import Client
from .paho_mqtt_client import MQTT_ERR_SUCCESS
from .xively_backoff import XivelyBackoff
from .xively_config import XivelyConfig
from .xively_message import XivelyMessage
from .xively_error_codes import XivelyErrorCodes as xec
from .xively_version import XivelyClientVersion

def return_if_inactive( *ret_args ):
    """
    This is a decorator that returns proper value if the main thread has been
    set as inactive. This decorator prevents infinite looping in case of calling client
    method from one of the callback.
    """
    def return_if_inactive_body( decorated_function ):
        def return_if_inactive_logic( self, *args, **kwargs ):
            if not self._alive:
                return ret_args
            else:
                return decorated_function( self, *args, **kwargs )
        return return_if_inactive_logic
    return return_if_inactive_body


class XivelyClient:

    """XivelyClient class is for connecting to and using Xively Services"""

    # classvariables
    last_connection_result_code = xec.XI_STATE_OK
    publish_count_until_last_stat_message = 0

    # callbacks

    @staticmethod
    def on_connect_finished(client, result):
        """called when the xively service responds to our connection request or when a connection error occurs.

        result -- a XivelyErrorCodes class member, possible values are :

            xec.XI_STATE_OK : Connection successful
            xec.XI_MQTT_UNACCEPTABLE_PROTOCOL_VERSION : Connection refused, wrong protocol
            xec.XI_MQTT_IDENTIFIER_REJECTED : Connection refused, invalid client id
            xec.XI_MQTT_SERVER_UNAVAILIBLE : Connection refused, server error
            xec.XI_MQTT_BAD_USERNAME_OR_PASSWORD : Connection refused, invalid credentials
            xec.XI_TLS_CONNECT_ERROR : Connection refused, TLS error"""
        pass

    @staticmethod
    def on_disconnect_finished(client, result):
        """called when the xively service responds to our disconnection request

        result -- the Xively Error Code, possible values are :

            xec.XI_STATE_OK : Connection successful"""
        pass

    @staticmethod
    def on_publish_finished(client, request_id):
        """called when a message that was to be sent using the publish() call has completed transmission to the broker.
        For messages with QoS levels 1 and 2, this means that the appropriate handshakes have completed. For QoS 0,
        this simply means that the message has left the client.

        request_id -- the identifier of the publish request"""
        pass

    @staticmethod
    def on_subscribe_finished(client, request_id, granted_qos):
        """called when the broker responds to a subscribe request.

        request_id -- the identifier of the subscribe request
        granted_qos -- the qos the service granted for the request"""
        pass

    @staticmethod
    def on_unsubscribe_finished(client, request_id):
        """called when the broker responds to an unsubscribe request.

        request_id -- the identifier of the unsubscribe request"""
        pass

    @staticmethod
    def on_message_received(client, message):
        """called when a message has been received on a topic that the client subscribes to. The message variable is a
        XivelyMessage instance that describes all of the message parameters."""
        pass


    # API functions

    def connect(self, options):
        """connect to the Xively Services.

        options -- connection options in a XivelyConnectionParameters instance

        returns -- nothing"""

        self._options = options
        self._options.client_id = self._options.username
        self._last_publish_count_send_time = 0

        if self._routine != self._routine_reconnect:

            # first connection
            if self._last_connection_time == 0:
                self._routine = self._routine_connect

            # backoff
            else :
                self._routine = self._routine_reconnect

        self._alive = True

        # start runloop if needed
        if self._thread == None :
            self._thread = threading.Thread( target = self._runloop , args = [ ] )
            self._thread.start()


    def join(self):
        try:
            while self._alive:
                self._thread.join(1.0)
        except KeyboardInterrupt:
            try:
                self._alive = False
                self._thread.join()
            except KeyboardInterrupt:
                pass


    def disconnect(self):
        """disconnect from the Xively Services.

        returns -- nothing"""

        self._mqtt.disconnect()


    # returns a success, request_id tuple
    @return_if_inactive(False,None)
    def subscribe(self, topics):
        """Subscribe the client to one or more topics.

        topics -- the topic(s) to subscribe to with qos levels

        returns -- (success,request_id)

        This function may be called in two different ways:

        String and integer tuple
        ------------------------
        e.g. subscribe(("my/topic", 1))

        List of string and integer tuples
        ------------------------
        e.g. subscribe([("my/topic", 0), ("another/topic", 2)])

        This allows multiple topic subscriptions in a single SUBSCRIPTION command, which is more efficient than using
        multiple calls to subscribe().

        The function returns a tuple (success, request_id), where success is a boolean indicating success, request_id
        is the request identifier for the subscribe request. The request_id value can be used to track the subscribe
        request by checking against the request_id argument in the on_subscribe_finished() callback if it is defined."""

        result, request_id = self._mqtt.subscribe(topics)

        if result != MQTT_ERR_SUCCESS:
            return True, request_id
        else:
            return False, request_id


    # returns a success, request_id tuple
    @return_if_inactive(False,None)
    def unsubscribe(self, topics):
        """Unsubscribe the client from one or more topics.

        topics -- the topic(s) to unsubscribe from

        returns -- (success,request_id)

        This function may be called in two different ways:

        String and integer tuple
        ------------------------
        e.g. subscribe(("my/topic", 1))

        List of string and integer tuples
        ------------------------
        e.g. subscribe([("my/topic", 0), ("another/topic", 2)])

        This allows multiple topic unsubscriptions in a single UNSUBSCRIPTION command, which is more efficient than
        using multiple calls to subscribe().

        The function returns a tuple (success, request_id), where success is a boolean indicating success, request_id
        is the request identifier for the subscribe request. The request_id value can be used to track the subscribe
        request by checking against the request_id argument in the on_subscribe_finished() callback if it is defined."""

        result, request_id = self._mqtt.unsubscribe(topics)

        if result != MQTT_ERR_SUCCESS:
            return True, request_id
        else:
            return False, request_id


    # returns a success, request_id tuple
    @return_if_inactive(False,None)
    def publish(self, topic, payload, qos, retain):
        """publish a message on a topic.

        This causes a message to be sent to the Xively Services and subsequently from the Services to any xively clients
        subscribing to matching topics.

        topic -- The topic that the message should be published on.
        payload -- The actual message to send. If not given, or set to None a zero length message will be used.
        Passing an int or float will result in the payload being converted to a string representing that number. If
        you wish to send a true int/float, use struct.pack() to create the payload you require.
        qos -- The quality of service level to use.
        retain -- If set to true, the message will be set as the "last known good"/retained message for the topic.

        returns -- (success,request_id)

        Returns a tuple (success, request_id), where success is a boolean indicating success, request_id is the
        request id for the publish request. The request_id value can be used to track the publish request by checking
        against the request_id argument in the on_publish_finished() callback if it is defined."""

        result, request_id = self._mqtt.publish(topic, payload, qos, retain)

        if result != MQTT_ERR_SUCCESS:
            return True, request_id
        else:
            return False, request_id


    @return_if_inactive(False,None)
    def publish_timeseries(self, topic, value, qos):

        """publish a float value on a topic marked as timeseries

        This causes a message with a float value to be sent to the Xively Services

        topic -- The topic that the message should be published on.
        value -- The actual value to send
        qos -- The quality of service level to use.

        returns -- (success,request_id)

        Returns a tuple (success, request_id), where success is a boolean indicating success, request_id is the
        request id for the publish request. The request_id value can be used to track the publish request by checking
        against the request_id argument in the on_publish_finished() callback if it is defined.

        Returns false as success if value is not a float"""

        if not isinstance(value, float):
            return False,0

        # convert float value to its binary representation
        payload = struct.pack('f', value)

        return self.publish(topic, bytearray( payload ), qos, False)


    @return_if_inactive(False,None)
    def publish_formatted_timeseries(self, topic, time, in_category, in_string_value, in_numeric_value, qos):

        """publish a float value on a topic marked as timeseries

        This causes a message with a float value to be sent to the Xively Services and stored in the database

        Unlike the standard float timeseries publication, this timeseries can include a category name, a string value
        and a numeric float value. At least one of these fields must be set. If you wish to omit any one of these fields
        then pass None as value to this function.

        The time value is also optional.  If provided the timeseires will be stored in the Xively database with the
        provided milliseconds since the epoch.
        If not provide (if it's None) then the Xively service will tag the time series data with the current server time

        NOTE: this function uses CSV for a message format internally. Therefore the following characters cannot be
        within a category or string_value:
            newline: \n
            carriage return: \r
            comma: ,
        If a new line, a carriage return, or a comma is detected, then this function will be return False

        topic -- The topic that the message should be published on.

        time -- Optional. The number of milliseconds since the epoch. If None, the Xively service will timestamp the
                timeseries with the server time.

        in_category -- Optional. The timeseries category as defined above.  This is a customer dependent value and has
                       no impact on how Xively handles the timeseries.
                       May be used in conjuction with numeric_value and string_value.

        in_string_value -- Optional. A field that will log a string value for the time series.
                           May be used in conjuction with nuermic_value and category.

        in_numeric_value -- Optional. A field that will log a float value for the time series.
                            May be used in conjuction with string_Value and category.

        qos -- The quality of service level to use.

        returns -- (success,request_id)

        Returns a tuple (success, request_id), where success is a boolean indicating success, request_id is the
        request id for the publish request. The request_id value can be used to track the publish request by checking
        against the request_id argument in the on_publish_finished() callback if it is defined.

        Returns false as success if in_numeric_value is not a float, time is not an int, in_category and
        in_string is longer than 1024 bytes"""

        # one of the custom parameters has to be defined
        if in_category == None and in_string_value == None and in_numeric_value == None :
            return False, 0

        payload = ""

        # add time as string
        if time != None :

            if not isinstance(time, int):
                return False, 0

            payload += str(time)

        payload += ","

        # add category if doesn't contain invalid characters
        if in_category != None:

            if len(bytearray(in_category, "utf8")) > 1024 or set( in_category ) & set( ",\r\n" ):
                return False, 0

            else :
                payload += in_category

        payload += ","

        # add numberic value
        if in_numeric_value != None:

            if not isinstance(in_numeric_value, float):
                return False, 0

            payload += str(in_numeric_value)

        payload += ","

        # add string value if doesn't contain invalid characters
        if in_string_value != None:

            if len(bytearray(in_string_value, "utf8")) > 1024 or set( in_string_value ) & set( ",\r\n" ):
                return False, 0

            else :
                payload += in_string_value

        return self.publish(topic, payload, qos, False)


    # timeout for paho main loop
    _XC_PAHO_LOOP_TIMEOUT = 1.0

    def __init__(self):

        XivelyBackoff.backoff_class = XivelyBackoff.XI_BACKOFF_CLASS_NONE

        self._cbHandler = XivelyCallbackHandler(self)
        self._boHandler = XivelyBackoff()
        self._coHandler = XivelyConfig()

        self._last_connection_time = 0
        self._last_cooldown_time = 0
        self._backoff_duration = 0

        self._hostindex = 0
        self._certindex = 0

        self._alive = True
        self._options = None
        self._disconnection_state = xec.XI_STATE_OK

        self._thread = None
        self._routine = None

    def __del__(self):

        self._cbHandler = None
        self._boHandler = None

    def _runloop(self):

        while self._alive:
            self._routine()

        self._thread = None

    def _mqtt_loop(self):
        try:
            self._mqtt.loop(timeout=self._XC_PAHO_LOOP_TIMEOUT)
        except ValueError as valueError:
            """ Write on closed or unwrapped SSL socket. is raised from ssl write function """
            #print("*** exception = " + str(valueError))
            pass
        except:
            raise

    def _routine_connecting(self):
        if time.time() - self._last_connection_time > float(self._options.connection_timeout):
            self._disconnection_state = xec.XI_STATE_TIMEOUT
            self._routine = self._routine_rejected
        else:
            self._mqtt_loop()


    def _routine_connected(self):
        print("_routine_connected")
        self._mqtt_loop()
        self._try_cooldown()


    def _routine_rejected(self):
        self._alive = False
        self._mqtt.reinitialise()
        self._cbHandler.on_connect_finished( self._disconnection_state )


    def _routine_disconnected(self):
        self._alive = False
        self._mqtt.reinitialise()
        self._cbHandler.on_disconnect_finished( self._disconnection_state )


    # do the real connection when backoff enables

    def _routine_connect(self):
        self._backoff_duration = 0
        self._last_connection_time = time.time()

        self._mqtt = Client( self._options.client_id , self._options.clean_session , None , paho_mqtt_client.MQTTv31 , self._options.use_websocket )
        self._mqtt.on_connect = lambda client, userdata, flag_or_result, result : self._mqtt_on_connect_finished(flag_or_result, result)
        self._mqtt.on_disconnect = lambda client, userdata, result : self._mqtt_on_disconnect_finished(result)
        self._mqtt.on_message = lambda client, userdata, message : self._mqtt_on_message_received(message)
        self._mqtt.on_publish = lambda client, userdata, mid: self._mqtt_on_publish_finished(mid)
        self._mqtt.on_subscribe = lambda client, userdata, mid, granted_qos: self._mqtt_on_subscribe_finished(mid, granted_qos)
        self._mqtt.on_unsubscribe = lambda client, userdata, mid: self._mqtt_on_unsubscribe_finished(mid)
        self._mqtt.username_pw_set(self._options.username, self._options.password)

        hosts = XivelyConfig.XI_MQTT_HOSTS
        certs = XivelyConfig.XI_MQTT_CERTS

        try:
            # TLSv1.2 by default
            use_tls_version = ssl.PROTOCOL_TLSv1_2
        except:
            # py2.7 has only TLSv1.0
            use_tls_version = ssl.PROTOCOL_TLSv1

        # setup TLS if host requires it
        if hosts[self._hostindex][2] :
            self._mqtt.tls_set(
                os.path.dirname( sys.modules[__name__].__file__ ) + "/certs/" + certs[self._certindex],
                tls_version=use_tls_version)

        # setup last will if present
        if self._options.will_message is not None:
            self._mqtt.will_set(self._options.will_topic, self._options.will_message, self._options.will_qos, self._options.will_retain)

        try:

            if not self._options.use_websocket :

                self._mqtt.connect(hosts[self._hostindex ][0],\
                                  hosts[self._hostindex ][1],\
                                  self._options.keep_alive)

            else:

                self._mqtt.connect(hosts[self._hostindex ][0],\
                                  XivelyConfig.XI_MQTT_WEBSOCKET_PORT,\
                                  self._options.keep_alive)

            self._routine = self._routine_connecting

        except ssl.SSLError as error:

            self._routine = self._routine_reconnect
            self._certindex += 1

            if self._certindex == len( certs) :

                self._certindex = 0
                self._disconnection_state = xec.XI_TLS_CONNECT_ERROR
                self._routine = self._routine_rejected

        except ssl.CertificateError as error:

            self._routine = self._routine_reconnect
            self._certindex += 1

            if self._certindex == len( certs) :

                self._certindex = 0
                self._disconnection_state = xec.XI_TLS_CERTIFICATE_ERROR
                self._routine = self._routine_rejected

        except socketerror as error:

            self._hostindex += 1

            if self._hostindex == len( hosts ):

                self._hostindex = 0
                self._disconnection_state = xec.XI_SOCKET_ERROR
                self._routine = self._routine_rejected


    # check backoff duration

    def _routine_reconnect(self):

        # get backoff_duration penalty if not present

        if self._backoff_duration == 0 :

            self._backoff_duration = XivelyBackoff.get_backoff_penalty()

        # connect if possible

        if time.time() - self._last_connection_time >= float(self._backoff_duration):

            self._routine = self._routine_connect

        time.sleep(1.0)


    def _mqtt_on_connected(self, previous_connection_result):

        XivelyBackoff.reset_last_update()

        self._routine = self._routine_connected
        self._cbHandler.on_connect_finished(xec.XI_STATE_OK)


    def _mqtt_on_connect_finished(self, flag_or_result, result=-1):
        # generate xiPy error code
        return_code = 0
        previous_connection_result = XivelyClient.last_connection_result_code
        xively_code = xec.XI_MQTT_CONNECT_UNKNOWN_RETURN_CODE

        if result > -1:
            return_code = result
        else:
            return_code = flag_or_result

        if return_code == 0x00:
            xively_code = xec.XI_STATE_OK

        elif return_code == 0x01:
            xively_code = xec.XI_MQTT_UNACCEPTABLE_PROTOCOL_VERSION

        elif return_code == 0x02:
            xively_code = xec.XI_MQTT_IDENTIFIER_REJECTED

        elif return_code == 0x03:
            xively_code = xec.XI_MQTT_SERVER_UNAVAILIBLE

        elif return_code == 0x04:
            xively_code = xec.XI_MQTT_BAD_USERNAME_OR_PASSWORD

        elif return_code == 0x05:
            xively_code = xec.XI_MQTT_NOT_AUTHORIZED

        elif return_code == 0x07:
            xively_code = xec.XI_TLS_CONNECT_ERROR

        # set internal state
        if xively_code == xec.XI_STATE_OK:
            self._mqtt_on_connected(previous_connection_result)

        else:
            self._disconnection_state = xively_code
            self._routine = self._routine_rejected

        XivelyClient.last_connection_result_code = xively_code


    def _mqtt_on_disconnect_finished(self, result):
        if result == 0:
            self._disconnection_state = xec.XI_STATE_OK
        elif result == 1:
            self._disconnection_state = xec.XI_CONNECTION_RESET_BY_PEER_ERROR

        if self._routine == self._routine_connecting :
            self._last_connection_time = 0
            self._routine = self._routine_rejected

        elif self._routine == self._routine_connected :
            self._last_connection_time = 0
            self._routine = self._routine_disconnected


    def _mqtt_on_message_received(self, message):

        xi_message = XivelyMessage()
        xi_message.qos = message.qos
        xi_message.topic = message.topic
        xi_message.payload = message.payload
        xi_message.request_id = message.mid

        self._cbHandler.on_message_received(xi_message)


    def _mqtt_on_publish_finished(self, request_id):
        XivelyClient.publish_count_until_last_stat_message += 1
        self._cbHandler.on_publish_finished(request_id)


    def _mqtt_on_subscribe_finished(self, request_id, granted_qos):

        self._cbHandler.on_subscribe_finished(request_id, granted_qos)


    def _mqtt_on_unsubscribe_finished(self, request_id):

        self._cbHandler.on_unsubscribe_finished(request_id)


    # cooldown backoff

    def _try_cooldown(self):

        if time.time() - self._last_cooldown_time >= 1.0 :
            XivelyBackoff.update_penalty()
            self._last_cooldown_time = time.time()
