#!/bin/bash

# Create certs directory if it doesn't exist
mkdir -p certs
cd certs

# Generate private key
openssl genrsa -out tls.key 2048

# Generate CSR configuration
cat > csr.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
CN = aiforenterprise.dev.internal
O = Cognizant

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = aiforenterprise.dev.internal
EOF

# Generate certificate
openssl req -x509 -new -nodes \
    -key tls.key \
    -sha256 -days 365 \
    -out tls.crt \
    -config csr.conf

# Create kubernetes secret
echo "Now run these kubectl commands to create the secret:"
echo "kubectl create namespace oauth2-proxy # if namespace doesn't exist"
echo "kubectl create secret tls oauth2-proxy-tls -n oauth2-proxy --key=tls.key --cert=tls.crt"
