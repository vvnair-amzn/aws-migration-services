# Custom HTTP/HTTPS Proxy Server

## Overview
This Python-based proxy server accepts internal traffic and routes it to the internet. It supports both HTTP and HTTPS protocols through a tunneling mechanism, making it suitable for various network environments including those preparing for AWS migrations.

## Features
- Supports both HTTP and HTTPS traffic
- Multi-threaded design for handling concurrent connections
- Detailed logging for troubleshooting
- Configurable timeout and buffer settings
- Connection pooling for improved performance
- Error handling with informative responses

## Prerequisites
- Python 3.6 or higher
- Basic understanding of networking concepts
- Root/admin privileges (if using ports below 1024)
- Network connectivity to target servers

## Installation

1. Clone or download the proxy server script:
bash
curl -o https_proxy_server.py https://raw.githubusercontent.com/yourusername/proxy-server/main/https_proxy_server.py

2. Make the script executable:
bash
chmod +x https_proxy_server.py

## Configuration
The proxy server can be configured by modifying the following variables at the top of the script:

- `LISTENING_ADDR`: The address to bind the server to (default: '0.0.0.0')
- `LISTENING_PORT`: The port to listen on (default: 8080)
- `BUFFER_SIZE`: Size of the data buffer (default: 8192)
- `MAX_CONNECTIONS`: Maximum number of concurrent connections (default: 100)
- `TIMEOUT`: Connection timeout in seconds (default: 60)

## Usage

### Starting the Proxy Server
bash
python3 https_proxy_server.py

### Configuring Clients to Use the Proxy

#### Command Line Tools
bash
export HTTP_PROXY="http://localhost:8080"
export HTTPS_PROXY="http://localhost:8080"

#### Web Browsers
Configure your browser's proxy settings to use:
- Proxy Host: localhost (or the IP address of the machine running the proxy)
- Proxy Port: 8080 (or your configured port)

#### Testing the Proxy
bash
curl -v -x http://localhost:8080 http://example.com

## Troubleshooting

### Common Issues and Solutions

1. **502 Bad Gateway**
   - Verify the target server is accessible
   - Check network connectivity
   - Ensure there are no firewall restrictions

2. **Connection Refused**
   - Confirm the proxy server is running
   - Verify the port is not in use by another application
   - Check firewall settings

3. **Slow Performance**
   - Adjust the buffer size
   - Increase the maximum connections if needed
   - Check network bandwidth

### Debugging
Increase the logging level by changing `logging.INFO` to `logging.DEBUG` in the script for more detailed logs.

## Security Considerations
- This proxy does not implement authentication
- Traffic is not encrypted between the client and proxy
- Consider running in a secure network environment
- Not recommended for production use without additional security measures

## AWS Migration Compatibility
This proxy can be useful during AWS migrations to:
- Test network connectivity to AWS endpoints
- Route traffic through specific paths
- Validate firewall and security group configurations
- Support Application Migration Service (MGN) connectivity requirements

## Author
Vijesh V

## Version
1.0.0
