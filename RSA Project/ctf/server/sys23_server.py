import socket
import threading
import RSA
import random

pub_key, priv_key = RSA.gen_key()

oracle_type = "OAEP"
soundness = False
soundness_probability = 0.05


def PCKS_Conforming(candidate):
    global priv_key
    dec_candidate = RSA.dec_msg(candidate,priv_key)
    bit_flag = (random.random() < soundness_probability) and soundness
    #flipping answer
    if bit_flag:
        if oracle_type == "OAEP":
            return not dec_candidate[:1] == b"\x00"
        else:
            if dec_candidate[:2] == b"\x00\x02":
                try:
                    if dec_candidate[2:].index(0x00) >= 11: #FFT
                        return not True
                    else: #A zero in first, FTT
                        return not oracle_type[1] == 'T'
                except ValueError: #No zeros..., TFT
                    return not oracle_type[0] == 'T'

            return not False

    else:
        if oracle_type == "OAEP":
            return dec_candidate[:1] == b"\x00"
        else:
            if dec_candidate[:2] == b"\x00\x02":
                try:
                    if dec_candidate[2:].index(0x00) >= 11:  # FFT
                        return True
                    else:  # A zero in first, FTT
                        return (oracle_type[1] == 'T')
                except ValueError:  # No zeros..., TFT
                    return (oracle_type[0] == 'T')
            return False


def handle_client(client_socket, addr):
    print(f"New connection from {addr}")

    try:
        message = "you fell from heaven?"

        # **Step 1: Send the Public Key (n, e)**
        n_bytes = pub_key[1].to_bytes((pub_key[1].bit_length() + 7) // 8, 'big')
        e_bytes = pub_key[0].to_bytes((pub_key[0].bit_length() + 7) // 8, 'big')

        client_socket.send(len(n_bytes).to_bytes(2, 'big'))  # Send length of n
        client_socket.send(n_bytes)  # Send n
        client_socket.send(len(e_bytes).to_bytes(2, 'big'))  # Send length of e
        client_socket.send(e_bytes)  # Send e

        # **Step 2: Send the Encrypted Message**
        temp_sniffed = RSA.enc_msg(message, pub_key,False)
        client_socket.send(len(temp_sniffed).to_bytes(4, 'big'))  # Send length of message
        client_socket.send(temp_sniffed)  # Send message

        # **Step 3: Handle Player Queries**
        while True:
            encrypted_data = client_socket.recv(2048)
            if not encrypted_data:
                break  # Client disconnected

            if PCKS_Conforming(encrypted_data):
                client_socket.send(b"Valid")
            else:
                client_socket.send(b"Invalid")

    except Exception as e:
        print(f"Error with {addr}: {e}")

    finally:
        client_socket.close()
        print(f"Connection closed for {addr}")


def start_server():
    global oracle_type, soundness

    oracle_type = "OAEP"  # Hardcoded for now
    soundness = False  # Hardcoded for now

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 15342))  # System port - 42069
    server_socket.listen(50)  # Allow multiple connections

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.daemon = True  # Automatically closes thread on exit
        client_thread.start()


start_server()
