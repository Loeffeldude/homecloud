# vpn-router/entrypoint.sh
#!/bin/bash
set -e

echo "Starting VPN router for $CONTAINER_NAME"

# Function to get container IP
get_container_ip() {
  curl -s --unix-socket /var/run/docker.sock \
    "http://localhost/containers/json" | \
    jq -r ".[] | select(.Names[] | contains(\"$CONTAINER_NAME\")) | .NetworkSettings.Networks.\"$NETWORK_NAME\".IPAddress"
}

# Function to add route
add_route() {
  local ip=$1
  echo "Adding route to $VPN_SUBNET via $ip"
  ip route add $VPN_SUBNET via $ip
}

# Function to delete route
delete_route() {
  local ip=$1
  echo "Removing route to $VPN_SUBNET via $ip"
  ip route del $VPN_SUBNET via $ip || true
}

# Setup cleanup on exit
cleanup() {
  echo "Cleaning up..."
  if [ -n "$CONTAINER_IP" ]; then
    delete_route "$CONTAINER_IP"
  fi
  exit 0
}

trap cleanup SIGTERM SIGINT SIGQUIT

# Wait for container to be ready
while true; do
  CONTAINER_IP=$(get_container_ip || echo "")

  if [ -n "$CONTAINER_IP" ]; then
    echo "Found container IP: $CONTAINER_IP"
    break
  fi

  echo "Waiting for container $CONTAINER_NAME..."
  sleep 2
done

# Add route
add_route "$CONTAINER_IP"

echo "Route established. Monitoring container..."

# Monitor container and update route if IP changes
while true; do
  sleep 10

  # Get current IP (with error handling)
  NEW_IP=$(get_container_ip || echo "")

  # If container disappeared, wait but don't exit
  if [ -z "$NEW_IP" ]; then
    echo "Container $CONTAINER_NAME not found! Waiting..."
    sleep 10
    continue
  fi

  # If IP changed, update route
  if [ "$NEW_IP" != "$CONTAINER_IP" ]; then
    echo "Container IP changed: $CONTAINER_IP → $NEW_IP"
    delete_route "$CONTAINER_IP"
    CONTAINER_IP="$NEW_IP"
    add_route "$CONTAINER_IP"
  fi
done

# This should never be reached - critical error
echo "CRITICAL ERROR: Infinite loop exited unexpectedly!"
exit 1
