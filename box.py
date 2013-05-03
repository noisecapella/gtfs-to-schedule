__author__ = 'schneg'

import binascii
import struct
class Box:
    """Usage:

    box = Box()

    box.add_int(3)
    box.add_int(-4)

    print("INSERT INTO table VALUES (%s)" % box.get_blob_string()")
    """
    def __init__(self):
        self.bytes = "" # this is hex

    def add_int(self, x):
        self.bytes += binascii.b2a_hex(struct.pack('>i', x))

    def add_ints(self, ints):
        self.add_int(len(ints))
        for i in ints:
            self.add_int(i)

    def add_float(self, f):
        self.bytes += binascii.b2a_hex(struct.pack('>f', f))

    def get_blob_string(self):
        return "X'" + self.bytes + "'"

