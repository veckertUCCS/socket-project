import socket
import os
import sys
from cryptography.fernet import Fernet
from cryptographic_components import *

# Initialize the necessary constants
HOST = "localhost"
PORT = 2001
BUFFER = 1024
CMD_SIZE = 4
data = None
USER = "ae5deb822e0d71992900471a7199d0d95b8e7c9d05c40a8245a281fd2c1d6684".encode()
PASS = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f".encode()
C_CERT = "eaee52b65a1925037aa2183c9779fa26020d46a586cd4a0469ab3930c386493d".encode()
S_CERT = "b0877a2466ba5a964048c67708ee335f9b04301b73e539b867b76f125bc2cb4d".encode()
TEST_KEY = "7IpGDicXFjJ8y69W4J1WexT17uzxrK9fVzyk0RcjBuk=".encode()

# Initialize the encryption/decryption engine
crypt_engine = Fernet(TEST_KEY)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Waiting for connection from client...")
client, addr = server.accept()
print("Connection request received from ", addr)
print("Performing credential exchange with client...")
client.send(crypt_engine.encrypt(S_CERT))
token = crypt_engine.decrypt(client.recv(BUFFER))
print("Connection successful!")
client.send("1".encode())



# Function to authenticate between client and server
def authenticate():
    print("Ready to authenticate...")
    # Initial exchange
    client.send("1".encode())

    # Receive username from client
    username = crypt_engine.decrypt(client.recv(1024))
    client.send("1".encode())
    
    # Receive password from client
    password = crypt_engine.decrypt(client.recv(1024))

    # If the username and password are correct, set atatus to 1; set it to 0 otherwise
    if username == USER and password == PASS:
        print("Valid Credentials!")
        status = "1"
    else:
        print("Invalid Credentials!")
        status = "0"
    # Send the status to the client and confirm receipt
    client.send(status.encode())
    client.recv(1)
    return

def send():
    print("Ready to receive file...")
    # Initial exchange
    client.send("1".encode())

    # Receive the filepath from the client and decode it
    filename = crypt_engine.decrypt(client.recv(BUFFER))
    filename = isolate_file_name(filename.decode())

    # Notify the server that the file name has been processed
    client.send("1".encode())

    # Receive the size of the file from the server
    file_size = int(crypt_engine.decrypt(client.recv(BUFFER)).decode())

    # Open the file for writing
    file = open("./files/"+filename, "wb")
    received_bytes = 0

    # Signal that the server is ready to receive information
    client.send("1".encode())
    # While the server still has data left to process
    while received_bytes < file_size:
        # Receive the data from the server
        info = client.recv(BUFFER)
        # Write the data to the file
        file.write(info)
        # Increment the amount of data that has been read
        received_bytes += BUFFER
        # Signal to the client that the next data block can be read
        client.send("1".encode()) 
    # When there is no more data, close the file and await the client's confirmation
    file.close()

    print("File Received!")

    if decrypt_file_from_transport("./files/"+filename, crypt_engine):
        print("Transmission Success!")
        status = "1"
    else:
        print("Transmission Failure! Aborting process...")
        os.remove("./files/"+filename)
        status = "0"
    client.recv(1)

    # Reply to the confirmation and return
    client.send(status.encode())
    return

def receive():
    print("Ready to send file...")
    # Initial exchange
    client.send("1".encode())

    # Receive file name and send file size
    filename = crypt_engine.decrypt(client.recv(BUFFER))
    encrypt_file_for_transport("./files/"+filename.decode(), crypt_engine)    

    file_size = os.path.getsize(os.getcwd()+"/files/"+filename.decode())
    client.send(crypt_engine.encrypt(str(file_size).encode()))

    # Wait for confirmation that the client is ready for data transfer
    client.recv(1)

    # Open the file for reading and read the first bit of data
    file = open("./files/"+filename.decode(), "rb")
    data = file.read(BUFFER)
    # Loop while there is data to transfer
    while data:
        # Send data to the client
        client.send(data)
        # Wait for the client to process all of their data
        client.recv(1)
        # Read the next bit of data
        data = file.read(BUFFER)

    # Close the file
    file.close()
    # Signal that the server is done transferring
    status = client.recv(1)
    print("File sent!")
    if status.decode() == "1":
        print("Transmission Success!")
        os.remove("./files/"+filename.decode())
    else:
        print("Transmission Failure! Aborting process...")
        decrypt_file_from_transport("./files/"+filename.decode(), crypt_engine)

    client.send("1".encode())
    return

# Function to list send the contents of a directory to the client
def list_directory():
    client.send("1".encode())
    client.recv(1)
    string = create_directory_string()
    client.send(crypt_engine.encrypt(string.encode()))
    print("Sent file list!")
    client.recv(1)
    return

# Function to close down the server
def exit():
    print("Exit request received, closing down...")
    client.close()
    server.close()
    print("Closing done!")
    return

# Function to create a list of the files in a directory in string format
def create_directory_string():
    file_list = os.listdir("./files")
    list_string = ""
    for item in file_list:
        list_string += item
        list_string += ","
    return list_string

# Function to isolate the name of the file from a file path
def isolate_file_name(filepath):
    path_list = filepath.split("/")
    return path_list[len(path_list) - 1]

while True:
    print("Awaiting command from client...")
    data = client.recv(CMD_SIZE).decode()
    if data == "AUTH":
        authenticate()
    elif data == "SEND":
        send()
    elif data == "RECV":
        receive()
    elif data == "LIST":
        list_directory()
    elif data == "EXIT":
        exit()
        break

    data = None
