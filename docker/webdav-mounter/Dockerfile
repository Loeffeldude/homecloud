FROM python:3.11-alpine

# Install davfs2, fuse, bash (bash needed for mounting scripts)
RUN apk add --no-cache davfs2 fuse bash curl

COPY webdav_mount.py /webdav_mount.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/mnt"]

ENTRYPOINT ["/entrypoint.sh"]
