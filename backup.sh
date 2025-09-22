#!/bin/bash

# --- Configuration ---
# The name of your Docker container for PostgreSQL (from docker-compose.yml)
CONTAINER_NAME="apex_postgres"

# The database user and name (from docker-compose.yml)
DB_USER="apexuser"
DB_NAME="apexdb"

# The local directory where backups will be stored
BACKUP_DIR="./database_backups"

# --- Script Logic ---

# Create the backup directory on your local machine if it doesn't exist
mkdir -p $BACKUP_DIR

# Create a timestamped filename for the backup file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="$BACKUP_DIR/${DB_NAME}_backup_${TIMESTAMP}.sql.gz"

echo "➡️ Starting backup of database '$DB_NAME'..."

# This command runs 'pg_dump' inside the Docker container.
# The output is then compressed with gzip and saved to the local file.
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME | gzip > $FILENAME

# Check the exit code of the previous command to confirm success
if [ $? -eq 0 ]; then
  echo "✅ Backup successful!"
  echo "   Saved to: $FILENAME"
else
  echo "❌ Backup failed!"
  # Remove the empty/failed backup file
  rm $FILENAME
fi
```eof
**How to Use This Script:**
1.  **Make it executable:** Open your terminal in the `apex/` directory and run this command once:
    ```bash
    chmod +x backup.sh
    ```
2.  **Run a backup:** Whenever you want to create a backup, run this command:
    ```bash
    ./backup.sh
    ```

**Production Note:** In a real production environment, you would use a scheduler like `cron` to run this script automatically every night.

We have now set up our backup script. Ready for the final point: **Monitoring for connection health and query performance**?