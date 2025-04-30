#!/usr/bin/env python3

import subprocess
import json
import os
import sys
import argparse


def run(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print(f"ERROR: Command {cmd} failed.")
        print(f"Stdout: {result.stdout.decode()}")
        print(f"Stderr: {result.stderr.decode()}")
        sys.exit(1)
    else:
        print(result.stdout.decode())


def setup_davfs2():
    conf_path = "/etc/davfs2/davfs2.conf"

    # Disable locks (helps with fuse mounts in containers)
    with open(conf_path, "a+") as f:
        f.seek(0)
        contents = f.read()
        if "use_locks 0" not in contents:
            f.write("use_locks 0\n")


def prepare_secrets(mounts):
    secret_path = "/etc/davfs2/secrets"
    lines = []

    for m in mounts:
        url = m["url"]
        username = m.get("username")
        password = m.get("password")

        if not username or not password:
            print(f"ERROR: Missing username or password for url {url}")
            sys.exit(1)

        lines.append(f"{url} {username} {password}")

    with open(secret_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    os.chmod(secret_path, 0o600)
    print(f"Written credentials to {secret_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Mount multiple WebDAV shares from JSON config"
    )
    parser.add_argument("--config", required=True, help="Path to JSON config file")

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Config file {args.config} not found!")
        sys.exit(1)

    with open(args.config, "r") as f:
        try:
            config = json.load(f)
        except Exception as e:
            print(f"Failed to parse JSON config: {e}")
            sys.exit(1)

    mounts = config.get("mounts")
    if not mounts or not isinstance(mounts, list):
        print("Config JSON should contain a 'mounts' list")
        sys.exit(1)

    setup_davfs2()
    prepare_secrets(mounts)

    for m in mounts:
        url = m["url"]
        target = m["target"]

        if not url or not target:
            print("Each mount must have 'url' and 'target' fields")
            sys.exit(1)

        # Ensure target dir exists
        os.makedirs(target, exist_ok=True)

        # Check if already mounted, unmount first (optional)
        result = subprocess.run(["mountpoint", "-q", target])
        if result.returncode == 0:
            print(f"{target} is already mounted, unmounting")
            run(["umount", target])

        print(f"Mounting {url} to {target} ...")
        run(["mount", "-t", "davfs", url, target, "-o", "rw"])

    print("All mounts successful.")


if __name__ == "__main__":
    main()
