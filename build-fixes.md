# Build Script Fixes

## Issues Found:
1. **Permission denied** - The remote backup directory doesn't exist or lacks permissions
2. **Circular foreign-key constraints** - ProductCategory has self-referential relationships

## Solutions:

### 1. Fix Permission Issues
Add directory creation before each scp command:
```bash
ssh $REMOTE_SERVER "mkdir -p $REMOTE_BACKUP_DIR"
```

### 2. Fix pg_dump Warnings
For data-only dumps with circular constraints, use `--disable-triggers`:
```bash
pg_dump -U shop_smart_user shop_smart -a -O -T django_migrations --disable-triggers -f /media/...
```

### 3. Alternative Solution
Instead of data-only dumps, use full dumps without the `-a` flag as suggested by pg_dump.

## Recommended Approach:
Use full dumps for all backups to avoid circular constraint issues:
1. Remove the `-a` flag from pg_dump commands
2. Keep the `-O` flag to avoid ownership issues
3. Keep the `-T django_migrations` to exclude migrations

This will create complete backups that can be restored without trigger issues.