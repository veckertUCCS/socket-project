from cryptography.fernet import Fernet
import hashlib

# Function to generate an encrypted bytestring from a plaintext bytestring using Fernet
def encrypt_data(data: bytes, engine: Fernet) -> bytes: 
    return engine.encrypt(data)

# Function to generate a decrypted bytestring from a ciphertext bytestring
def decrypt_data(data: bytes, engine: Fernet) -> bytes:
    return engine.decrypt(data)

# Function to generate a tag from a bytestring using a SHA256 hash from hashlib
def tag_data(data: bytes) -> bytes:
    placeholder = data
    return hashlib.sha256(placeholder).hexdigest()

# Function to validate a message-tag pair by recomputing the hash value
def validate_tag(data: bytes, tag: bytes) -> bool:
    placeholder = data
    if hashlib.sha256(data).hexdigest() == tag:
        return True
    else:
        return False

# Function to read the contents of a file from a specified path as bytes
def read_bytes_from_file(file_path: str) -> bytes:
    file = open(file_path, "rb")
    bytestring = file.read()
    file.close()
    return bytestring

# Function to encrypt a file in preparation for transport
def encrypt_file_for_transport(file_path: str, crypto_engine: Fernet) -> None:
    #TODO figure out where to place initialization of cryptographic components
    content_bytes = read_bytes_from_file(file_path)
    encrypted_content = encrypt_data(content_bytes, crypto_engine)
    content_tag = hashlib.sha256(encrypted_content).hexdigest().encode()
    file = open(file_path, "wb")
    file.write(encrypted_content+",".encode()+content_tag)
    file.close()

# Function to decrypt a file that has been received
def decrypt_file_from_transport(file_path: str, crypto_engine: Fernet) -> None:
    #TODO figure out where to place initialization of cryptographic components
    file = open(file_path, "r")
    file_contents = file.read()
    file.close()
    file_contents_list = file_contents.split(",")
    if file_contents_list[1] == hashlib.sha256(file_contents_list[0].encode()).hexdigest():
        print("Validation Successful!")
        decrypted_contents = crypto_engine.decrypt(file_contents_list[0].encode())
        file = open(file_path, "w")
        file.write(decrypted_contents.decode())
        file.close()
        return True
    else:
        print("Validation Failed!")
        return False
