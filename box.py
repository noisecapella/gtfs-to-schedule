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
    def __init__(self, bytes=None):
        if bytes is None:
            self.bytes = "" # this is hex
        else:
            self.bytes = bytes
            self.pos = 0

    def read_short(self):
        s = self.bytes[self.pos:self.pos+2]
        self.pos += 2
        return struct.unpack('>H', s)[0]

    def read_int(self):
        s = self.bytes[self.pos:self.pos+4]
        self.pos += 4
        return struct.unpack('>i', s)[0]

    def read_byte(self):
        s = self.bytes[self.pos:self.pos+1]
        self.pos += 1
        return struct.unpack('>B', s)[0]

    def read_string(self):
        l = self.read_byte()
        chunk = self.bytes[self.pos:self.pos+l]
        self.pos += l
        return chunk

    def add_string(self, s):
        if type(s) != str:
            raise Exception("Invalid type: %s" % str(type(s)))
        if len(s) > 0xff:
            raise Exception("String too long")
        self.add_byte(len(s))
        self.bytes += self.to_str(binascii.b2a_hex(s))

    def add_short(self, x):
        if x < 0 or x > 0xffff:
            raise Exception("x out of range")
        self.bytes += self.to_str(binascii.b2a_hex(struct.pack('>H', x)))

    def add_byte(self, x):
        if x < 0 or x > 0xff:
            raise Exception("x out of range")
        self.bytes += self.to_str(binascii.b2a_hex(struct.pack('>B', x)))

    def add_int(self, x):
        self.bytes += self.to_str(binascii.b2a_hex(struct.pack('>i', x)))

    def add_ints(self, ints):
        self.add_int(len(ints))
        for i in ints:
            self.add_int(i)

    def add_float(self, f):
        self.bytes += self.to_str(binascii.b2a_hex(struct.pack('>f', f)))

    def to_str(self, b):
        return b.decode("utf-8")

    def get_blob_string(self):
        return "X'" + self.bytes + "'"


