#!/bin/bash
set -e

CONFIG_FILE="/config/mounts.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file $CONFIG_FILE not found!"
  exit 1
fi

echo "Starting WebDAV mounts from config..."

# Run python mount script
python3 /webdav_mount.py --config "$CONFIG_FILE"

echo "All mounts completed."

# Keep container alive
tail -f /dev/null
