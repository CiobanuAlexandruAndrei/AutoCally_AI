#!/bin/bash

# Install mkcert if not already installed
if ! command -v mkcert &> /dev/null; then
    echo "mkcert not found, please install it first"
    exit 1
fi

# Initialize mkcert
mkcert -install

# Generate certificates for localhost and your Docker network IPs
mkcert -key-file server.key -cert-file server.cert localhost 172.20.0.10 172.20.0.11 172.20.0.14