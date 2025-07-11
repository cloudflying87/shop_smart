#!/bin/bash

# Default values
BACKUP_all=false
BACKUP_data=false
REBUILD=false
RESTORE=false
ALL=false
SOFT_REBUILD=false
REMOTE_SERVER="davidhale87@172.16.205.4"
REMOTE_BACKUP_DIR="/halefiles/Coding/ShopSmartBackups"

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
    echo "  -s, --soft        Soft rebuild (backup DB, rebuild app, keep DB)"
    echo "  -o, --restore     Restore database from backup"
    echo ""
    echo "Example:"
    echo "  $0 -d 2023-05-13 -b -c -s  # Backup, copy, and transfer files with date 2023-05-13"
    echo "  $0 -a -d 2023-05-13       # Run all steps with date 2023-05-13"
    echo "  $0 -r -u -m               # Rebuild, restart containers and run migrations"
    echo "  $0 -s -d 2023-05-13       # Soft rebuild with backup but keep database"
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
        -s|--soft)
            SOFT_REBUILD=true
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
if [[ ("$BACKUP_data" = true || "$BACKUP_all" = true || "$RESTORE" = true || "$SOFT_REBUILD" = true) && -z "$USER_DATE" ]]; then
    echo "Error: Date (-d or --date) is required for backup/restore/soft-rebuild operations"
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
echo "Soft Rebuild: $SOFT_REBUILD"
echo "Restore: $RESTORE"
echo "-----------------------------------"

# Backup database
if [ "$BACKUP_data" = true ]; then
    echo "Taking data only SQL up database with data only: $USER_DATE"
    
    # Ensure containers are running
    echo "Starting containers if not running..."
    sudo docker compose up -d
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -a -O -T django_migrations --disable-triggers -f /media/shop_smartbackup_${USER_DATE}_data.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_data.sql /media/ 
    # Create directory if it doesn't exist
    ssh $REMOTE_SERVER "mkdir -p $REMOTE_BACKUP_DIR"
    scp /media/shop_smartbackup_${USER_DATE}_data.sql $REMOTE_SERVER:$REMOTE_BACKUP_DIR/
fi

# Copy backup files from container to host
if [ "$BACKUP_all" = true ]; then
    echo "Backing up and copying all data. $USER_DATE"
    
    # Ensure containers are running
    echo "Starting containers if not running..."
    sudo docker compose up -d
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -a -O -T django_migrations --disable-triggers -f /media/shop_smartbackup_${USER_DATE}_data.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_data.sql /media/ 
    

    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}.sql 
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -c -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}_clean.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}.sql /media/ 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_clean.sql /media/ 
    echo "Transferring backup files to remote server"
    # Create directory if it doesn't exist
    ssh $REMOTE_SERVER "mkdir -p $REMOTE_BACKUP_DIR"
    scp /media/shop_smartbackup_${USER_DATE}_data.sql $REMOTE_SERVER:$REMOTE_BACKUP_DIR/
    scp /media/shop_smartbackup_${USER_DATE}.sql $REMOTE_SERVER:$REMOTE_BACKUP_DIR/
    scp /media/shop_smartbackup_${USER_DATE}_clean.sql $REMOTE_SERVER:$REMOTE_BACKUP_DIR/
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
    echo "Building and starting containers"
    sudo docker compose build --no-cache
    sudo docker compose up -d
    
    echo "Waiting for containers to be ready..."
    sleep 15
    
    # Check if web container is running
    if ! sudo docker compose ps web | grep -q "Up"; then
        echo "Error: Web container is not running. Checking status..."
        sudo docker compose ps
        exit 1
    fi
    
    echo "Running Django migrations"
    # Ensure web service is ready
    echo "Collecting static files..."
    sudo docker compose exec web python manage.py collectstatic --noinput
    echo "Making migrations..."
    sudo docker compose exec web python manage.py makemigrations 
    echo "Applying migrations..."
    sudo docker compose exec web python manage.py migrate
    echo "Django setup completed successfully" 
    
fi

# Soft rebuild - backup database and rebuild app without deleting database
if [ "$SOFT_REBUILD" = true ]; then
    echo "Starting soft rebuild - backing up database and rebuilding app"
    
    # Ensure containers are running for backup
    echo "Starting containers if not running..."
    sudo docker compose up -d
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    # First, backup the database
    echo "Backing up database with date: $USER_DATE"
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -a -O -T django_migrations --disable-triggers -f /media/shop_smartbackup_${USER_DATE}_data_soft.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_data_soft.sql /media/ 
    
    # Also create a full backup for safety
    sudo docker exec -it shop_smart-db-1 pg_dump -U shop_smart_user shop_smart -O -T django_migrations -f /media/shop_smartbackup_${USER_DATE}_full_soft.sql 
    sudo docker cp shop_smart-db-1:/media/shop_smartbackup_${USER_DATE}_full_soft.sql /media/ 
    
    echo "Stopping and removing containers (keeping database)"
    sudo docker stop shop_smart-web-1 
    sudo docker stop shop_smart-nginx-1 
    sudo docker rm shop_smart-web-1 
    sudo docker rm shop_smart-nginx-1 
    
    # Clean up images but keep volumes (including postgres_data)
    sudo docker image prune -a -f 
    sudo docker volume remove shop_smart_static_volume 
    sudo docker volume remove shop_smart_media_volume
    # Note: We're NOT removing shop_smart_postgres_data volume
    
    echo "Building and starting containers with existing database"
    sudo docker compose build
    sudo docker compose up -d 
    
    echo "Waiting for containers to be ready..."
    sleep 15
    
    # Check if web container is running
    if ! sudo docker compose ps web | grep -q "Up"; then
        echo "Error: Web container is not running. Checking status..."
        sudo docker compose ps
        exit 1
    fi
    
    echo "Running Django migrations"
    echo "Collecting static files..."
    sudo docker compose exec web python manage.py collectstatic --noinput
    echo "Making migrations..."
    sudo docker compose exec web python manage.py makemigrations 
    echo "Applying migrations..."
    sudo docker compose exec web python manage.py migrate
    echo "Django setup completed successfully" 
    
    echo "Soft rebuild completed - database preserved"
fi

# Restore database
if [ "$RESTORE" = true ]; then
    echo "Restoring database from backup"
    
    # Ensure containers are running
    echo "Starting containers if not running..."
    sudo docker compose up -d
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    sudo docker cp /media/shop_smartbackup_${USER_DATE}_data.sql shop_smart-db-1:/media 
    sudo docker exec -it shop_smart-db-1 psql -d shop_smart -U shop_smart_user -f /media/shop_smartbackup_${USER_DATE}_data.sql 
fi

echo "Build script completed successfully!"