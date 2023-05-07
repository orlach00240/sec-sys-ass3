import socket
import time
import random
import struct
import hashlib
import binascii


##### Construct the version message ######

# Binary encode the sub-version
def create_sub_version():
    sub_version = "/Satoshi:0.7.2/"
    return b'\x0F' + sub_version.encode()

# Binary encode the network addresses
def create_network_address(ip_address, port):
    # Convert the packed binary IP address to a bytes object
    ip_address_bytes = socket.inet_aton(ip_address)
    # Concatenate the two binary values into a single bytes object
    addr_bytes = bytearray.fromhex("00000000000000000000ffff") + ip_address_bytes
    # Pack the bytes object and port into a binary format
    return struct.pack(">16sH", bytes(addr_bytes), port)

# Create the TCP request object
def create_message(magic, command, payload):
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[0:4]
    return(struct.pack('L12sL4s', magic, command.encode(), len(payload), checksum) + payload)

# Create the "version" request payload
def create_payload_version(peer_ip_address):
    version = 60002
    services = 1
    timestamp = int(time.time())
    addr_local = create_network_address('0.0.0.0', 8333)
    addr_peer = create_network_address(peer_ip_address, 8333)
    nonce = random.getrandbits(64)
    start_height = 0
    payload = struct.pack('<LQQ26s26sQ16sL', version, services, timestamp, addr_peer,
                          addr_local, nonce, create_sub_version(), start_height)
    return(payload)

##### Construct the verack #####

# Create the "verack" request message
def create_message_verack():
    return bytearray.fromhex("f9beb4d976657261636b000000000000000000005df6e0e2")

##### Fetch the details of a transaction ####

# Create the "getdata" request payload
def create_payload_getdata(tx_id):
    count = 1
    type = 1
    hash = bytearray.fromhex(tx_id)
    payload = struct.pack('<bb32s', count, type, bytes(hash))
    return(payload)

###### Print out binary data as hex #########

# Print request/response data
def print_response(command, request_data, response_data):
    print("")
    print("Command: " + command)
    print("Request:")
    print(binascii.hexlify(request_data))
    print("Response:")
    print(binascii.hexlify(response_data))

####### Wait for responses ######

def read_n_bytes(sock, n):
    data = b''
    while len(data) < n:
        packet = None
        try:
            packet = sock.recv(n - len(data))
        except socket.error as e:
            print("Socket error: {}".format(e))
            break
        if not packet:
            break
        data += packet
    return data

####### Main method to connect to bitcoin node #######

if __name__ == '__main__':
    # Set constants
    magic_value = 0xd9b4bef9
    tx_id = "00000000000000000001ad087e12dec3fabc1ece9f0ece2605504c109bf4daa2"
    peer_ip_address = '50.107.191.62'
    peer_tcp_port = 8333
    buffer_size = 4096

    # Create Request Objects
    version_payload = create_payload_version(peer_ip_address)
    version_message = create_message(magic_value, "version", version_payload)
    verack_message = create_message_verack()
    getdata_payload = create_payload_getdata(tx_id)
    getdata_message = create_message(magic_value, 'getdata', getdata_payload)

    # Establish TCP Connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((peer_ip_address, peer_tcp_port))

    # Send message "version"
    s.send(version_message)
    response_data = read_n_bytes(s, buffer_size)
    print_response("version", version_message, response_data)

    # Send message "verack"
    s.send(verack_message)
    response_data = read_n_bytes(s, buffer_size)
    print_response("verack", verack_message, response_data)

    # Send message "getdata"
    s.send(getdata_message)
    response_data = read_n_bytes(s, buffer_size)
    print_response("getdata", getdata_message, response_data)

    # Close the TCP connection
    s.close()