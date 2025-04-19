# vpn-router/Dockerfile
FROM alpine:latest

# Install required packages
RUN apk add --no-cache iproute2 curl jq bash

# Copy our script
COPY router-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV CONTAINER_NAME="wireguard-homecloud"
ENV VPN_SUBNET="10.13.13.0/24"
ENV NETWORK_NAME="homecloud-vpn"

ENTRYPOINT ["/entrypoint.sh"]
