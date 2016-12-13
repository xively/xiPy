====
xiPy
====

The official pythonic library for the next-gen Xively platform. Built on top of `paho-mqtt python client`_.

.. _`paho-mqtt python client`: https://pypi.python.org/pypi/paho-mqtt/1.1

Install
-------

There are two options:

- using pip:

.. code:: 

  pip install xiPy

- Clone or download this repo.

Usage
-----
 Connect
--------

.. code:: python

  from xiPy.xively_connection_parameters import XivelyConnectionParameters
  from xiPy.xively_client import XivelyClient
  from xiPy.xively_config import XivelyConfig

  XivelyConfig.XI_MQTT_HOSTS = [ ("my_company.broker.xively.com", 8883, True) ]
  
  params = XivelyConnectionParameters()
  params.username = "my_deviceid"
  params.password = "my_password"

  client = XivelyClient()
  
  client.connect(params)
  
  client.join()

This connects client to Xively. How to get Xively credentials? See `PUB and SUB with the Python library`_.

.. _`PUB and SUB with the Python library`: https://developer.xively.com/docs/publish-and-subscribe-with-the-python-library

 Set connection finished callback
---------------------------------

.. code:: python

  def my_on_connect_finished(client, result):
    print("connection resultcode = " + str(result) + ", error codes: xiPy/xi_error_codes.py\n")

  client.on_connect_finished = my_on_connect_finished

xiPy error codes: xively_error_codes.py_

.. _xively_error_codes.py: xiPy/xively_error_codes.py

 Callbacks
----------

These can be overridden with custom actions:

.. code:: python

  client.on_connect_finished(client, result)
  client.on_disconnect_finished(client, result)
  client.on_publish_finished(client, request_id)
  client.on_subscribe_finished(client, request_id, granted_qos)
  client.on_unsubscribe_finished(client, request_id)
  client.on_message_received(client, message)


API
---

.. code:: python

  client.connect(options)
  client.disconnect()
  client.publish(topic, payload, qos, retain)
  client.publish_timeseries(topic, value, qos)
  client.publish_formatted_timeseries(topic, time, category, string_value, numeric_value, qos)
  client.subscribe(topic_qos_list)
  client.unsubscribe(topic_list)


Features
--------
- Python 2.7 and Python 3.x support
- TLS connection to Xively, TLS1.2 for Python 3.x, TLS1.0 for Python 2.7.x
- Websocket Support

License
-------
This library is Open Source, under the `BSD 3-Clause license`_.

.. _`BSD 3-Clause license`: LICENSE.md
