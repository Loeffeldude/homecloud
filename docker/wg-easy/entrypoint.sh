#!/bin/bash

iptables -t nat -A POSTROUTING -s 10.42.42.0/24 -o wg0 -j MASQUERADE

exec "$@"
