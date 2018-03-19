# Copyright (c) 2003-2016, Xively. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

class XivelyCallbackHandler:

    def __init__(self, delegate):

        self.delegate = delegate
        self.topicsToListeners = {}


    def __del__(self):

        self.delegate = None
        self.topicsToListeners = None


    def on_connect_finished(self, result):

        for listeners in self.topicsToListeners.values():
            for listener in listeners :
                listener.on_connect_finished(result)

        self.delegate.on_connect_finished(self.delegate,result)


    def on_disconnect_finished(self, result):

        for listeners in self.topicsToListeners.values():
            for listener in listeners :
                listener.on_disconnect_finished(result)

        self.delegate.on_disconnect_finished(self.delegate,result)


    def on_message_received(self, message):

        if message.topic != None:

            if message.topic in self.topicsToListeners:

                for listener in self.topicsToListeners[message.topic]:
                    listener.on_message_received(message)

            else :
                self.delegate.on_message_received(self.delegate, message)


    def on_subscribe_finished(self, requestid, granted_qos):

        self.delegate.on_subscribe_finished(self.delegate, requestid, granted_qos)


    def on_unsubscribe_finished(self, requestid):

        self.delegate.on_unsubscribe_finished(self.delegate, requestid)


    def on_publish_finished(self, requestid):

        self.delegate.on_publish_finished(self.delegate, requestid)


    def add_listener(self, topic, listener):

        if topic not in self.topicsToListeners:
            self.topicsToListeners[topic] = []

        self.topicsToListeners[topic].append(listener)


    def remove_listener(self, topic, listener):

        if topic in self.topicsToListeners :
            self.topicsToListeners[topic].remove(listener)
