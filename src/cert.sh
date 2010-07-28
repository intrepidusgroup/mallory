#!/bin/bash

set -e
set -x

if [ -z "$1" ]; then
	echo "Syntax: ./cert.sh www.example.com"
	exit 1
fi

DOMAIN=$1

OPENSSL=openssl

if [ ! -d ca ]; then
	mkdir ca
	
	# Generating CA private key and self-signed certificate
	
	$OPENSSL req -x509 -newkey rsa:2048 -days 7671 -outform pem -set_serial 1 -out ca/ca.cer -config openssl-ca.cnf
	
	# Get private key and certificate info
	
	$OPENSSL x509 -in ca/ca.cer -outform der -out ca/ca.cer.der
	$OPENSSL x509 -text -in ca/ca.cer -out ca/ca.cer.info
	
	# Set up CA files
	
	mkdir ca/certs
	echo '02' > ca/serial
	touch ca/index
fi

#
# Certificate
#

mkdir -p certs

# Generating private key and CSR

$OPENSSL genrsa -out certs/$DOMAIN.key 2048

cp openssl-cert.cnf certs/$DOMAIN.cnf
echo "commonName = $DOMAIN" >> certs/$DOMAIN.cnf

$OPENSSL req -new -key certs/$DOMAIN.key -out certs/$DOMAIN.csr -config certs/$DOMAIN.cnf
$OPENSSL req -text -in certs/$DOMAIN.csr -out certs/$DOMAIN.csr.info

# Sign the certificate

$OPENSSL ca -batch -config openssl-ca.cnf -in certs/$DOMAIN.csr -out certs/$DOMAIN.cer
$OPENSSL x509 -text -in certs/$DOMAIN.cer -out certs/$DOMAIN.cer.info
