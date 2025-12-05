#!/usr/bin/env bash
# Helper bash build script for V10 (Git Bash / WSL)
# Usage: ./build.sh [SystemCheck]
NAME=${1:-SystemCheck}

set -e

if [ ! -f ./icon.ico ]; then
  echo "icon.ico not found in project root. Place icon.ico next to this script."
  exit 1
fi

ICON="$(pwd)/icon.ico"

mkdir -p build build/temp release
cp -f "$ICON" build/icon.ico

echo "Running PyInstaller..."
pyinstaller --onefile --noconsole --uac-admin --icon="$ICON" --name="$NAME" --distpath=./release --specpath=./build --workpath=./build/temp V10.py

if [ -f ./.env ]; then
  cp -f ./.env ./release/.env
  echo ".env copied to ./release"
else
  echo "Warning: .env not found in project root. Remember to copy .env into release after build."
fi

echo "Build script finished."
