import socket
import threading
import time
import os
import sys
from datetime import datetime

currentTime = ""

def available_port(host, port): #Check if a port is available on the given host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    if (sock.connect_ex((host, port)) == 0):
        return available_port(host, port + 1)
    else:
        sock.close()
        return port    

HOST = '127.0.0.1'  # Localhost
PORT = 8000 # other than 80
PORT = available_port(HOST,PORT)

# set the http header and log head to file
def getHeader(status_code, file_type, last_modified):
    header = ''
    currentTime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())

    if status_code == 200:
        header += 'HTTP/1.1 200 OK\r\n'
    elif status_code == 304:
        header += 'HTTP/1.1 304 Not Modified\r\n'
    elif status_code == 400:
        header += 'HTTP/1.1 400 Bad Request\r\n'
    elif status_code == 403:
        header += 'HTTP/1.1 403 Forbidden\r\n'
    elif status_code == 404:
        header += 'HTTP/1.1 404 Not Found\r\n'
    elif status_code == 415:
        header += 'HTTP/1.1 415 Unsupported Media Type\r\n'

    header += f"Date: {currentTime}\r\n"
    header += "Connection: keep-alive\r\n"
    header += "Keep-Alive: timeout=10, max=100\r\n"
    header += f"Last-Modified: {last_modified}\r\n"

    if file_type == 'html':
        header += 'Content-Type: text/html\r\n'
    elif file_type in ['jpg', 'jpeg', 'png']:
        header += f'Content-Type: image/{file_type}\r\n'
    else:
        header += 'Content-Type: ' + file_type

    header += '\r\n'    
    log_header_str = ''.join([f"[{line}]" for line in header.split('\r\n') if line])  # Format headers in one line
    with open(os.path.join(os.getcwd(), "log.txt"), "a") as log_file:
        log_file.write(log_header_str + '\n')

    return header

# handle Last-Modified header field
def last_modified(file_path):
    # Get the last modified time in seconds since epoch
    last_modified_time = os.path.getmtime(file_path)
    return time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(last_modified_time))

# Handle the client request
def webServer(client_socket, client_address):
    persistent_connection = False
    while True:
        try:
            # Receive the request from the client
            request = client_socket.recv(4096).decode()
            #print(request)
            array = request.split('\n')
            modif_time_from_cache = None
            if ('If-Modified-Since:' in request):
                temp = array[-3].split(' ')[1:]
                modif_time_from_cache = " ".join(temp)
                modif_time_from_cache = modif_time_from_cache.split('\r')[0]
                print("If-Modified-Since: " + modif_time_from_cache)

            if not request:
                print("No message received, closing connection...")
                client_socket.close()
                break

            # Parse the request method
            request_method = request.split(' ')[0]
            print("Method: " + request_method)

            # Set timeout for 10 seconds
            if not persistent_connection:
                persistent_connection = True
                client_socket.settimeout(10)

            if request_method == "GET" or request_method == "HEAD":
                try:
                    # Get the requested file from the website address
                    file_requested = request.split(' ')[1]
                    if file_requested == "/":
                        file_requested = "/index.html"

                    file_type = file_requested.split('.')[1]
                    print("Request: " + file_requested + "\n")  

                except TimeoutError:
                    print("Timeout reached, closing connection...")
                    client_socket.close()
                    break    

                except Exception as e:
                    print("Error getting file type/requested file")
                    print("Closing client socket...")
                    client_socket.close()
                    break
                
                # point to the file path
                file_path = "./web" + file_requested

                if file_type == 'html':
                    try:
                        last_modified_time = last_modified(file_path)
                        if request_method == "GET":
                            file = open(file_path, 'r')
                            response_content = file.read()
                            file.close()
                            # with open(file_path, 'r') as file:
                            #     response_content = file.read()
                            response = getHeader(200, file_type, last_modified_time)
                            status_code = 200
                        elif modif_time_from_cache and (datetime.strptime(last_modified_time, "%a, %d %b %Y %H:%M:%S") < datetime.strptime(modif_time_from_cache, "%a, %d %b %Y %H:%M:%S")):
                            print("304 Not Modified")
                            response = getHeader(304, file_type, last_modified_time)
                            status_code = 304     

                    except FileNotFoundError:
                        print("404 File Not Found")
                        response = getHeader(404, file_type, 'N/A')
                        status_code = 404
                    except PermissionError:
                        print("403 Forbidden")
                        response = getHeader(403, file_type, 'N/A')
                        status_code = 403
                    except Exception as e:
                        print("400 Bad Request")
                        response = getHeader(400, file_type, 'N/A')
                        status_code = 400

                    if request_method == "GET" and status_code == 200:
                        print("Header: \n" + response)
                        #client_socket.send(response.encode())
                        #client_socket.send(response_content.encode())
                        client_socket.send((response + response_content).encode())

                    else:
                        print("Header: \n" + response)
                        client_socket.send(response.encode())

                elif file_type in ["jpg", "jpeg", "png"]:
                    try:
                        last_modified_time = last_modified(file_path)
                        if request_method == "GET":
                            file = open(file_path, 'rb')
                            response_content = file.read()
                            file.close()
                            response = getHeader(200, file_type, last_modified_time)
                            status_code = 200
                        elif (datetime.strptime(last_modified_time, "%a, %d %b %Y %H:%M:%S") < datetime.strptime(modif_time_from_cache, "%a, %d %b %Y %H:%M:%S")):
                            print("304 Not Modified")
                            response = getHeader(304, file_type, last_modified_time)
                            status_code = 304
                        
                    except FileNotFoundError:
                        print("404 File Not Found")
                        response = getHeader(404, file_type, 'N/A')
                        status_code = 404
                    except PermissionError:
                        print("403 Forbidden")
                        response = getHeader(403, file_type, 'N/A')
                        status_code = 403
                    except Exception as e:
                        print("400 Bad Request")
                        response = getHeader(400, file_type, 'N/A')
                        status_code = 400

                    if request_method == "GET" and status_code == 200:
                        print("Header: \n" + response)
                        client_socket.send(response.encode())
                        client_socket.send(response_content)
                    else:
                        print("Header: \n" + response)
                        client_socket.send(response.encode())  

                else:
                    print("415 Unsupported Media Type")
                    response = getHeader(415, file_type, 'N/A')
                    status_code = 415
                       
                if persistent_connection:
                    print("Continue to receive requests.")
                else:
                    print("Closing client socket due to end of connection.")
                    client_socket.close()
                    break
            else:
                print("Closing client socket...")
                client_socket.close()
                break            

        except socket.timeout:
            print("Timeout, closing connection...")
            client_socket.close()
            break

# Create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind((HOST, PORT))    # "Socket binded to xxx  "
    print("Running on http://127.0.0.1:" +str(PORT))
except Exception as e:
    print("Bind failed. Error: %s" % str(e))
    s.close()
    sys.exit(1)

s.listen(5)  # Listen for incoming connections
print("Socket is listening...")    

while True:
    # Accept a connection
    client_socket, client_address = s.accept()
    print("Connection from: ", client_address, "\n")

    # Handle the client in a separate thread
    client_handler = threading.Thread(target=webServer, args=(client_socket,client_address))
    client_handler.start()

