#!/usr/bin/env bash
set -e -o pipefail

# Usage:
#   ./run_nordic_file.sh /full/path/in_bold.nii.gz /full/path/out_bold.nii.gz /full/path/to/NORDIC_Raw-main

if [ $# -ne 3 ]; then
  echo "Usage: $0 /full/path/in_bold.nii.gz /full/path/out_bold.nii.gz /full/path/to/NORDIC_Raw-main" >&2
  exit 1
fi

IN_NII="$1"
OUT_NII="$2"
NORDIC_PATH="$3"

if [ ! -f "$IN_NII" ]; then
  echo "ERROR: input not found: $IN_NII" >&2
  exit 1
fi

if [ ! -d "$NORDIC_PATH" ]; then
  echo "ERROR: NORDIC_PATH not found: $NORDIC_PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT_NII")"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

matlab -batch "addpath('$SCRIPT_DIR'); NORDIC_run_single_file('$IN_NII','$OUT_NII','$NORDIC_PATH');"