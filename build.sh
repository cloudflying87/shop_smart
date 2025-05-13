#!/bin/bash

# Default values
BACKUP_all=false
BACKUP_data=false
REBUILD=false
RESTORE=false
ALL=false

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  -d, --date DATE   Date for database filenames (required for backup/restore operations)"
    echo "  -a, --all         Run all steps"
    echo "  -b, --backup      Only Backs up data.sql"
    echo "  -t, --backupall   Backs up and copies the 3 different files."
    echo "  -r, --rebuild     Rebuild containers (stop, remove, prune)"
    echo "  -o, --restore     Restore database from backup"
    echo ""
    echo "Example:"
    echo "  $0 -d 2023-05-13 -b -c -s  # Backup, copy, and transfer files with date 2023-05-13"
    echo "  $0 -a -d 2023-05-13       # Run all steps with date 2023-05-13"
    echo "  $0 -r -u -m               # Rebuild, restart containers and run migrations"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--date)
            USER_DATE="$2"
            shift 2
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -b|--data)
            BACKUP_data=true
            shift
            ;;
        -t|--backupall)
            BACKUP_all=true
            shift
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -o|--restore)
            RESTORE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# If ALL is set, enable all options
if [ "$ALL" = true ]; then
    BACKUP_all=true
    REBUILD=true
    RESTORE=true
fi

# Check if date is provided when needed
if [[ ("$BACKUP_data" = true || "$BACKUP_all" = true || "$RESTORE" = true) && -z "$USER_DATE" ]]; then
    echo "Error: Date (-d or --date) is required for backup/restore operations"
    show_help
    exit 1
fi

# Set default date format if needed
if [ -z "$USER_DATE" ]; then
    USER_DATE=$(date +%Y-%m-%d)
fi

# Display selected operations
echo "Running build with the following options:"
echo "Date: $USER_DATE"
echo "Backup: $BACKUP_all"
echo "Rebuild: $REBUILD"
echo "Restore: $RESTORE"
echo "-----------------------------------"

# Backup database
if [ "$BACKUP_data" = true ]; then
    echo "Taking data only SQL up database with data only: $USER_DATE"
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -a -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}_data.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_data.sql /media/ 
    scp /media/shop_smartbackup_${USER_DATE}_data.sql davidhale87@172.16.205.4:/halefiles/Coding/LogbookDBBackups 
fi

# Copy backup files from container to host
if [ "$BACKUP_all" = true ]; then
    echo "Backing up and copying all data. $USER_DATE"
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -a -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}_data.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_data.sql /media/ 
    

    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}.sql 
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -c -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}_clean.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}.sql /media/ 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_clean.sql /media/ 
    echo "Transferring backup files to remote server"
    scp /media/shop_smartbackup_${USER_DATE}_data.sql davidhale87@172.16.205.4:/halefiles/Coding/LogbookDBBackups
    scp /media/shop_smartbackup_${USER_DATE}.sql davidhale87@172.16.205.4:/halefiles/Coding/LogbookDBBackups 
    scp /media/shop_smartbackup_${USER_DATE}_clean.sql davidhale87@172.16.205.4:/halefiles/Coding/LogbookDBBackups 
fi

# Change to project directory
cd /home/davidhale87/docker/shop_smart 

# Pull latest changes
git pull 

# Rebuild containers
if [ "$REBUILD" = true ]; then
    echo "Stopping and removing containers"
    sudo docker stop shop_smart-db-1 
    sudo docker stop shop_smart-web-1 
    sudo docker stop shop_smart-nginx-1 
    sudo docker rm shop_smart-db-1 
    sudo docker rm shop_smart-web-1 
    sudo docker rm shop_smart-nginx-1 
    sudo docker image prune -a -f 
    sudo docker volume remove shop_smart_static_volume 
    sudo docker volume remove shop_smart_postgres_data
    sudo docker volume remove shop_smart_media_volume
    sudo docker volume prune -f
    echo "Starting containers"
    sudo docker compose up -d 
    echo "Running Django migrations"
    sudo docker compose -f docker-compose.yml exec web python manage.py collectstatic --noinput
    sudo docker compose -f docker-compose.yml exec web python manage.py makemigrations 
    sudo docker compose -f docker-compose.yml exec web python manage.py migrate 
fi

# Restore database
if [ "$RESTORE" = true ]; then
    echo "Restoring database from backup"
    sudo docker cp /media/shop_smartbackup_${USER_DATE}_data.sql shop_smart-db-1:/media 
    sudo docker exec -it shop_smart-db-1 psql -d shop_smart -U shop_smart_user -f /media/shop_smartbackup_${USER_DATE}_data.sql 
fi

echo "Build script completed successfully!"