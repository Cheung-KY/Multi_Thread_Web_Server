Multi-Threaded Web Server
Cheung Kei Yau

#Usage
1. put the request source files into folder ./web
2. type "py source_code_23088621d.py" on terminal to start the server program.
3. copy the website with port and visit this website on client

If the host already has a Web server running, use a port other than port 80.
The default port for the program is 8000.

#Features
	- Multi-threaded Web server
	- Proper request and response message exchanges
	- GET command for both text files and image files
	- HEAD command
	- Six types of response statuses
		- 200 OK
        - 304 Not Modified
		- 400 Bad Request
        - 403 Forbidden
		- 404 File Not Found
        - 415 Unsupported Media Type
	- Last-Modified and If-Modified-Since header fields

	- Keep-Alive header field

