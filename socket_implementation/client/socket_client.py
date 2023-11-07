import socket, sys, os, hashlib
from cryptography.fernet import Fernet
from cryptographic_components import *

# Initialize the necessary constants
ADDRESS = "localhost"
PORT = 2001
BUFFER = 1024
C_CERT = "eaee52b65a1925037aa2183c9779fa26020d46a586cd4a0469ab3930c386493d".encode()
S_CERT = "b0877a2466ba5a964048c67708ee335f9b04301b73e539b867b76f125bc2cb4d".encode()
TEST_KEY = "7IpGDicXFjJ8y69W4J1WexT17uzxrK9fVzyk0RcjBuk=".encode()

crypt_engine = Fernet(TEST_KEY)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Function to connect the client to the server
def connect():
    try:
        print("Performing credential exchange with server...")
        client.connect((ADDRESS, PORT))
        token = crypt_engine.decrypt(client.recv(BUFFER))
        client.send(crypt_engine.encrypt(C_CERT))
        client.recv(1)
        print("Connection successful!")
    except:
        print("Failed")

# Function to close down the client
def exit():
    print("Sending exit request to server and closing down...")
    client.send("EXIT".encode())
    client.close()
    print("Closing done!")
    return

# Function to send a file from the client to the server
def send(filepath: str):
    print("Ready to send file...")
    # Initial exchange
    client.send("SEND".encode())
    client.recv(1)
    
    #Send the filepath to the server and await response
    client.send(crypt_engine.encrypt(filepath.encode()))
    client.recv(1)

    # Get the file ready for encrypted transport
    encrypt_file_for_transport(filepath, crypt_engine)

    # Get the size of the file and send it to the server
    file_size = os.path.getsize(filepath)
    client.send(crypt_engine.encrypt(str(file_size).encode()))

    # Confirm that the server has received the file size
    client.recv(1)

    # Open the file and begin reading information
    file = open(filepath, "rb")
    data = file.read(BUFFER)

    # While there is data left to read
    while data:
        # Send the data to the server
        client.send(data)
        # Wait for the server to indicate that it has handled the data block
        client.recv(1)
        # Attempt to read more data from the file
        data = file.read(BUFFER)
    # When the transfer is done, notify the server
    file.close()
    print("File Sent!")
    client.send("1".encode())

    # Wait for the server to confirm, then remove the file
    status = client.recv(1)
    if status.decode() == "1":
        print("Transmission Success!")
        os.remove(filepath)
    else:
        print("Transmission Failure! Aborting process...")
        decrypt_file_from_transport(filepath, crypt_engine)
    return

def receive(filename: str):
    print("Ready to receive file.")
    # Initial exchange
    client.send("RECV".encode())
    client.recv(1)

    # Send file name and receive file size
    client.send(crypt_engine.encrypt(filename.encode()))
    file_size = int(crypt_engine.decrypt(client.recv(BUFFER)).decode())

    # Create a new file for writing data into
    file = open("./files/"+filename, "wb")
    received_bytes = 0

    # Send that the client is ready for data transmission
    client.send("1".encode())

    # Loop to write bytes of data to file
    while received_bytes < file_size:
        # Receive the data
        info = client.recv(BUFFER)
        # Write the data to the file
        file.write(info)
        # Increment the number of bytes received
        received_bytes += BUFFER
        # Signal that client is ready for more data
        client.send("1".encode()) 
    # Close the file
    file.close()
    print("File received!")
    if decrypt_file_from_transport("./files/"+filename, crypt_engine):
        print("Transmission Success!")
        status = "1"
    else:
        print("Transmission Failure! Aborting process...")
        os.remove("./files/"+filename)
        status = "0"
    # Wait for the signal that the server is done
    client.send(status.encode())
    client.recv(1)
    return

def list_directory():
    # Initial exchange
    client.send("LIST".encode())
    client.recv(1)

    # Confirm that client is ready for transmission
    client.send("1".encode())

    # Receive string from server
    string = crypt_engine.decrypt(client.recv(1024))
    # Create a list from the received string
    dir_list = create_file_list(string.decode())

    # Notify the server that the client is done
    client.send("1".encode())

    # Return the created list
    return dir_list

# Function to authenticate between client and server
def authenticate(username: str, password: str):
    print("Sending credentials...")
    # Initial exchange
    client.send("AUTH".encode())
    client.recv(1)

    # Send hashed username to server
    client.send(crypt_engine.encrypt(hashlib.sha256(username.encode()).hexdigest().encode()))
    client.recv(1)

    # Send hashed password to server and receive completion status
    client.send(crypt_engine.encrypt(hashlib.sha256(password.encode()).hexdigest().encode()))
    status = client.recv(1)

    # Confirm the receipt of status
    client.send("1".encode())

    # If the status is success, return true; return false otherwise
    if status.decode() == "1":
        print("Authentication successful!")
        return True
    else:
        print("Authentication failed!")
        return False

# Function to return a list of each filename in a string
def create_file_list(file_string):
    return file_string.split(",")

def acceptGUICommand(command: str, parameter = ""):
    if command == "CONN":
        connect()
    elif command == "AUTH":
        if authenticate(parameter[0], parameter[1]):
            return True
        else:
            return False
    elif command == "SEND":
        send(parameter)
    elif command == "RECV":
        receive(parameter)
    elif command == "LIST":
        return list_directory()
    elif command == "EXIT":
        exit()
    else:
        print("Invalid Command")