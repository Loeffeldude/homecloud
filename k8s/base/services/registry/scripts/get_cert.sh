#!/bin/bash

CERT_URL="https://auth.loeffelmeister.de/realms/loeffel/protocol/openid-connect/certs"


echo "-----BEGIN CERTIFICATE-----"
curl -s "$CERT_URL" | \
    jq -r '.keys[] | select(.use == "sig" and .alg == "RS256") | .x5c[0]'
echo "-----END CERTIFICATE-----"
