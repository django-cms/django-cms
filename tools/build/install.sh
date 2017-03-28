#!/bin/bash

set -e

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

bash ${BASEDIR}/node.sh
