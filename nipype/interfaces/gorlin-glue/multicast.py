#!/usr/bin/env python
#
# Send/receive UDP multicast packets.
# Requires that your OS kernel supports IP multicast.
#
# Usage:
#   mcast -s (sender, IPv4)
#   mcast -s -6 (sender, IPv6)
#   mcast    (receivers, IPv4)
#   mcast  -6  (receivers, IPv6)

MYPORT = 8123
MYGROUP_4 = '225.0.0.250'
MYGROUP_6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
MYTTL = 1 # Increase to reach other networks

import struct
import socket

class MultiSend(object):
    def __init__(self, group):
        self._addrinfo = addrinfo = socket.getaddrinfo(group, None)[0]
    
        self._s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    
        # Set Time-to-live (optional)
        ttl_bin = struct.pack('@i', MYTTL)
        if addrinfo[0] == socket.AF_INET: # IPv4
            self._s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        else:
            self._s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
    
    def encode(self, struct_or_format, *data):
        """Send a structure of data
        will be faster with a compiled struct.Struct object, but string format
        is okay too
        """
        try:
            self.send(struct_or_format.pack(*data))
        except AttributeError:
            self.send(struct.pack(struct_or_format, *data))
    def send(self, data):
        """Sends raw string/byte data"""
        #self._s.sendto(data + '\0', (self._addrinfo[4][0], MYPORT))
        self._s.sendto(data, (self._addrinfo[4][0], MYPORT))

class MultiReceive(object):

    def __init__(self, group):
        """Creates an object to receive multicasts from a group"""
        # Look up multicast group address in name server and find out IP version
        self.__addrinfo = socket.getaddrinfo(group, None)[0]

            
        try:
            group_bin = socket.inet_pton(self.__addrinfo[0], self.__addrinfo[4][0])
        except AttributeError:
            group_bin = socket.inet_aton(self.__addrinfo[4][0]) # Windows doesn't have pton
        self.__group_bin = group_bin
        
         # Join group
        if self.__addrinfo[0] == socket.AF_INET: # IPv4
            self.__mreq = self.__group_bin + struct.pack('=I', socket.INADDR_ANY)
        else:
            #May not work due to inet_aton only supporting IPv4
            self.__mreq = group_bin + struct.pack('@I', 0)
        self.flush()

    def flush(self):
        """Empties the receive buffer (by creating new socket!!)"""
        try:
            self._s.close()
        except AttributeError:
            pass
        
        # Create a socket
        self._s = socket.socket(self.__addrinfo[0], socket.SOCK_DGRAM)
        
        # Allow multiple copies of this program on one machine
        # (not strictly needed)
        self._s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind it to the port
        self._s.bind(('', MYPORT))

        # Join group
        if self.__addrinfo[0] == socket.AF_INET: # IPv4
            self._s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.__mreq)
        else:
            #May not work due to inet_aton only supporting IPv4
            self._s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, self.__mreq)
            
    def receive(self, buffsize):
        """Receives raw string/byte data"""
        data = self._s.recv(buffsize)
        #while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
        return data
    def decode(self, struct_or_format):
        """Receives and returns tuple according to struct format
        Will be faster as a compiled struct.Struct object      
        """
        try:
            return struct_or_format.unpack(self.receive(struct_or_format.size))
        except AttributeError:
            return struct.unpack(struct_or_format, self.receive(struct.calcsize(struct_or_format)))
        


def testSender():
    return MultiSend(MYGROUP_4)
def testReceiver():
    return MultiReceive(MYGROUP_4)