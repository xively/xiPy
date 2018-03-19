# Copyright (c) 2003-2016, Xively. All rights reserved.
# This is part of Xively Python library, it is under the BSD 3-Clause license.

import time
import random
from .xively_error_codes import XivelyErrorCodes as xec

class XivelyBackoff:

    XI_BACKOFF_CLASS_NONE = 0
    XI_BACKOFF_CLASS_RECOVERABLE = 1

    xi_backoff_lut = [1, 2, 4, 8, 32, 64, 128, 256, 512]
    xi_decay_lut = [4, 4, 8, 16, 30, 30, 30, 30, 30 ]

    last_update = 0
    backoff_class = 0
    backoff_lut_i = 0

    # get the current penalty time

    @classmethod
    def get_backoff_penalty( cls ):

        prev_i = max( cls.backoff_lut_i - 1, 0 )
        curr_val = cls.xi_backoff_lut[ cls.backoff_lut_i ]
        prev_val = cls.xi_backoff_lut[ prev_i ]
        half_prev_val = int( prev_val / 2 )

        return curr_val + random.randint( -half_prev_val, half_prev_val )


    @classmethod
    def _increase_penalty(cls):

        cls.backoff_lut_i = min( ( cls.backoff_lut_i + 1 ) , len( cls.xi_backoff_lut ) - 1 )

        XivelyBackoff.last_update = int( time.time() )


    @classmethod
    def _decrease_penalty(cls):

        cls.backoff_lut_i = max( cls.backoff_lut_i - 1, 0 )


    @classmethod
    def update_penalty(cls):

        if XivelyBackoff.backoff_lut_i > 0: # There is no point in checking if lut_i == 0

            if int( time.time() ) - cls.last_update > cls.xi_decay_lut[ cls.backoff_lut_i ]:
                if cls.backoff_class == cls.XI_BACKOFF_CLASS_NONE:
                    cls._decrease_penalty()
                cls.last_update = int( time.time() )


    @classmethod
    def reset(cls):

        cls.backoff_lut_i = 0
        cls.last_update = int( time.time() )


    @classmethod
    def reset_last_update(cls):

        cls.last_update = int( time.time() )


    @classmethod
    def on_connect_finished(cls,result):

        if result != xec.XI_STATE_OK : cls._increase_penalty()


    @classmethod
    def on_disconnect_finished(cls,result):

        if result == xec.XI_BACKOFF_TERMINAL: cls._increase_penalty()


    @classmethod
    def on_message_received(cls,message):

        pass

# for standalone testing
if __name__ == '__main__':

    counter = 0

    while True:

        if counter < 3:

            XivelyBackoff.on_connect_finished(xec.XI_SOCKET_ERROR)

        else :

            XivelyBackoff.update()

        time.sleep(1)
        counter += 1
