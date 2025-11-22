#!/bin/sh

# This script is the container's entrypoint.
# It first seeds the data file and then runs the main application.

# Define the source and destination for the library data.
SOURCE_DATA_FILE="standards_library" # Use a relative path, which is more robust.
DEST_DATA_FILE="/tmp/standards_library/library.json"

# This is the definitive data seeding logic. It runs ONCE when a new container starts.
# It explicitly checks if the destination file is missing before attempting to create and copy.
if [ ! -f "$DEST_DATA_FILE" ]; then
    mkdir -p "$(dirname "$DEST_DATA_FILE")"
    cp "$SOURCE_DATA_FILE" "$DEST_DATA_FILE"
fi

# The 'exec' command is crucial. It replaces the shell process with the streamlit process.
# This means Streamlit becomes PID 1 and can correctly receive signals like SIGINT and SIGTERM.
exec streamlit run standards_editor.py --server.port $PORT --server.address=0.0.0.0 --server.enableXsrfProtection=false --server.headless=true