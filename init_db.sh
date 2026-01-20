#!/bin/bash

# Initialize SQLite database for RSS Summarizer on Amazon Linux 2
# Usage: ./init_db.sh

set -e

DB_FILE="news.db"
SQL_FILE="init_db.sql"

echo "=========================================="
echo "RSS Summarizer Database Initialization"
echo "=========================================="

# Check if sqlite3 is installed
if ! command -v sqlite3 &> /dev/null; then
    echo "SQLite3 not found. Installing..."
    sudo yum install -y sqlite
fi

# Backup existing database if it exists
if [ -f "$DB_FILE" ]; then
    BACKUP_FILE="news.db.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backing up existing database to $BACKUP_FILE"
    cp "$DB_FILE" "$BACKUP_FILE"
fi

# Execute SQL script
if [ -f "$SQL_FILE" ]; then
    echo "Executing SQL initialization script..."
    sqlite3 "$DB_FILE" < "$SQL_FILE"
    echo "Database initialized successfully!"
else
    echo "Error: $SQL_FILE not found"
    exit 1
fi

# Set proper permissions
chmod 664 "$DB_FILE"

echo "=========================================="
echo "Database setup complete!"
echo "Categories: 5"
echo "RSS Feeds: 7"
echo "Topics: 9"
echo "System Config: 4"
echo "=========================================="
