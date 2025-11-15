#!/bin/sh

# This script is the container's entrypoint.
# It sets up the environment and then runs the main application.

# Define the source and destination for the library data.
SOURCE_DATA_FILE="/home/appuser/app/standards_library"
DEST_DATA_DIR="/tmp/standards_library"
DEST_DATA_FILE="$DEST_DATA_DIR/library.json"

# Seed the data directory. If the library.json doesn't exist in the temporary writable
# directory, copy the original from the container image to seed it.
mkdir -p "$DEST_DATA_DIR"
cp -n "$SOURCE_DATA_FILE" "$DEST_DATA_FILE"

# The 'exec' command is crucial. It replaces the shell process with the streamlit process.
# This means Streamlit becomes PID 1 and can correctly receive signals like SIGINT and SIGTERM.
exec streamlit run standards_editor.py --server.port $PORT --server.address=0.0.0.0 --server.enableXsrfProtection=false --server.headless=true