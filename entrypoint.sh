#!/bin/sh

# This script is the container's entrypoint.
# It first seeds the data file and then runs the main application.

# Define the source and destination for the library data.
SOURCE_DATA_FILE="/app/standards_library/library.json"
DEST_DATA_FILE="/tmp/standards_library/library.json"

# This is the definitive data seeding logic. It runs ONCE when a new container starts.
# It explicitly checks if the destination file is missing before attempting to create and copy.
if [ ! -f "$DEST_DATA_FILE" ]; then
    mkdir -p "$(dirname "$DEST_DATA_FILE")"
    if [ -f "$SOURCE_DATA_FILE" ]; then
        cp "$SOURCE_DATA_FILE" "$DEST_DATA_FILE"
    else
        echo "Warning: Source file $SOURCE_DATA_FILE not found. Starting with empty library."
    fi
fi

# Execute the command passed to the docker container (CMD)
exec "$@"