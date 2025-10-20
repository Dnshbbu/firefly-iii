# Building Custom Docker Container for Firefly III

Complete guide for creating and running your own custom Docker container from Firefly III source code.

## Overview

This guide walks you through building Firefly III from source using a custom Docker setup. Unlike the author's pre-built images, this approach allows you to:

- Modify source code and rebuild
- Customize any component
- Build both v1 and v2 frontend assets
- Full control over the entire stack

## What Was Created

A complete custom Docker setup has been created in the repository root:

```
firefly-iii/
├── Dockerfile                      # Multi-stage build for app
├── docker-compose.custom.yml       # Custom compose configuration
├── .dockerignore                   # Build optimization
├── .env.docker.example            # Environment template
└── docker/                        # Configuration files
    ├── README.md                  # Detailed documentation
    ├── entrypoint.sh              # Container startup script
    ├── php.ini                    # PHP configuration
    └── nginx.conf                 # Nginx config (optional)
```

## Architecture

### Multi-Stage Docker Build

The Dockerfile uses a 3-stage build process:

1. **Stage 1: Frontend Builder**
   - Node.js 22 Alpine
   - Builds both v1 (Vue 2) and v2 (Alpine.js) assets
   - Optimized with npm workspaces

2. **Stage 2: Composer Builder**
   - Composer 2 image
   - Installs PHP dependencies
   - No dev dependencies for smaller size

3. **Stage 3: Production Runtime**
   - PHP 8.4-FPM Alpine
   - All required PHP extensions
   - Copies built assets from stage 1 & 2
   - Minimal final image size

### Services Stack

- **app**: Firefly III (built from source)
- **db**: PostgreSQL 16
- **importer**: Data Importer (official image)
- **cron**: Scheduled tasks (recurring transactions)

## Quick Start (TL;DR)

```bash
# 1. Configure environment
cp .env.docker.example .env.docker
# Edit .env.docker with your settings (APP_KEY, DB_PASSWORD, etc.)

# 2. Build and start
docker-compose -f docker-compose.custom.yml build
docker-compose -f docker-compose.custom.yml up -d

# 3. Access
# Firefly III: http://localhost:8080
# Data Importer: http://localhost:8081
```

## Detailed Setup Instructions

### Step 1: Prerequisites

Install Docker and Docker Compose:

```bash
# Check versions
docker --version        # Should be 20.10+
docker-compose --version # Should be 2.0+

# On Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-v2

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### Step 2: Configure Environment

```bash
# Navigate to project root
cd /mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii

# Copy environment template
cp .env.docker.example .env.docker

# Generate secure APP_KEY (32 characters)
openssl rand -base64 32
# Example output: vXZ8fK3mN9pQ2wR5tY6uI7oP8aS9dF0g

# Generate STATIC_CRON_TOKEN (32 characters)
openssl rand -hex 16
# Example output: 3f8e9d4c2b1a5e6f7c8d9a0b1c2d3e4f

# Edit .env.docker
nano .env.docker
```

**Required settings in .env.docker:**

```bash
# MUST CHANGE THESE:
APP_KEY=paste_your_generated_32_char_key_here
DB_PASSWORD=your_secure_database_password
STATIC_CRON_TOKEN=paste_your_generated_32_char_token

# SHOULD CHANGE THESE:
SITE_OWNER=your_email@example.com
APP_URL=http://localhost:8080
TZ=Your/Timezone

# OPTIONAL:
FIREFLY_III_LAYOUT=v1  # or v2 for experimental layout
APP_ENV=production
APP_DEBUG=false
```

### Step 3: Build the Image

```bash
# Build the application image (takes 5-10 minutes first time)
docker-compose -f docker-compose.custom.yml build

# You'll see three build stages:
# [1/3] STEP 1/X: Building frontend assets...
# [2/3] STEP 2/X: Installing PHP dependencies...
# [3/3] STEP 3/X: Creating production image...
```

### Step 4: Start Services

```bash
# Start all services in detached mode
docker-compose -f docker-compose.custom.yml up -d

# Watch logs during first startup
docker-compose -f docker-compose.custom.yml logs -f app

# You should see:
# ✓ Database connection established
# ✓ Running database migrations...
# ✓ Firefly III started successfully!
```

### Step 5: Access and Setup

1. **Open Firefly III**: http://localhost:8080
2. **Register your account** (first account becomes admin)
3. **Complete your profile**

### Step 6: Setup Data Importer (Optional)

1. In Firefly III, go to **Options** → **Profile** → **OAuth**
2. Click **Create New Token**
3. Give it a name (e.g., "Data Importer")
4. Copy the generated token
5. Add to `.env.docker`:
   ```bash
   FIREFLY_III_ACCESS_TOKEN=your_token_here
   ```
6. Restart importer:
   ```bash
   docker-compose -f docker-compose.custom.yml restart importer
   ```
7. Access Data Importer: http://localhost:8081

## Making Code Changes

This is where custom Docker setup shines - you can modify source and rebuild!

### Method 1: Full Rebuild (Recommended)

```bash
# 1. Make your code changes
nano app/Http/Controllers/HomeController.php

# 2. Rebuild the app service
docker-compose -f docker-compose.custom.yml build app

# 3. Restart with new image
docker-compose -f docker-compose.custom.yml up -d app

# Or combine steps 2-3:
docker-compose -f docker-compose.custom.yml up -d --build app
```

### Method 2: Development Mode (Active Development)

For frequent changes, mount source code as volume:

1. Edit `docker-compose.custom.yml`, uncomment under `app` service:
   ```yaml
   volumes:
     - ./:/var/www/html:cached
   ```

2. Restart:
   ```bash
   docker-compose -f docker-compose.custom.yml restart app
   ```

3. Now changes are live! (PHP changes take effect immediately)

4. For frontend changes:
   ```bash
   docker-compose -f docker-compose.custom.yml exec app bash
   npm --workspace resources/assets/v1 run watch
   ```

### What Gets Rebuilt

- **Backend PHP changes**: Always requires rebuild (or dev mode)
- **Frontend v1/v2 changes**: Requires rebuild (or manual npm run)
- **Configuration changes** (docker/php.ini, etc.): Requires rebuild
- **Environment changes** (.env.docker): Just restart

## Common Operations

### View Logs

```bash
# All services
docker-compose -f docker-compose.custom.yml logs -f

# Just the app
docker-compose -f docker-compose.custom.yml logs -f app

# Last 100 lines
docker-compose -f docker-compose.custom.yml logs --tail=100 app
```

### Execute Commands in Container

```bash
# Open bash shell
docker-compose -f docker-compose.custom.yml exec app bash

# Run artisan commands
docker-compose -f docker-compose.custom.yml exec app php artisan cache:clear
docker-compose -f docker-compose.custom.yml exec app php artisan migrate
docker-compose -f docker-compose.custom.yml exec app php artisan tinker

# Check PHP version
docker-compose -f docker-compose.custom.yml exec app php -v
```

### Database Operations

```bash
# Backup database
docker-compose -f docker-compose.custom.yml exec db pg_dump -U firefly firefly > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.custom.yml exec -T db psql -U firefly firefly

# Access PostgreSQL shell
docker-compose -f docker-compose.custom.yml exec db psql -U firefly -d firefly

# Run SQL query
docker-compose -f docker-compose.custom.yml exec db psql -U firefly -d firefly -c "SELECT * FROM users;"
```

### Stop and Clean Up

```bash
# Stop services (keeps volumes)
docker-compose -f docker-compose.custom.yml down

# Stop and remove volumes (DELETE ALL DATA!)
docker-compose -f docker-compose.custom.yml down -v

# Remove built images
docker rmi firefly-iii-custom:latest

# Complete cleanup
docker-compose -f docker-compose.custom.yml down -v --rmi all
```

## Switching Frontend Layouts

```bash
# Edit .env.docker
nano .env.docker

# Change this line:
FIREFLY_III_LAYOUT=v2  # or v1

# Restart app
docker-compose -f docker-compose.custom.yml restart app

# Clear browser cache
```

## Performance Optimization

### Enable Redis Cache

1. Edit `docker-compose.custom.yml`, uncomment `redis` service
2. Edit `.env.docker`:
   ```bash
   CACHE_DRIVER=redis
   SESSION_DRIVER=redis
   REDIS_HOST=redis
   ```
3. Restart:
   ```bash
   docker-compose -f docker-compose.custom.yml up -d
   ```

### Production Optimizations

```bash
# In .env.docker:
APP_ENV=production
APP_DEBUG=false

# Cache config files
docker-compose -f docker-compose.custom.yml exec app php artisan config:cache
docker-compose -f docker-compose.custom.yml exec app php artisan route:cache
docker-compose -f docker-compose.custom.yml exec app php artisan view:cache
```

## Troubleshooting

### Build Fails

```bash
# Clear build cache
docker-compose -f docker-compose.custom.yml build --no-cache

# Check Docker disk space
docker system df

# Clean up old images
docker system prune -a
```

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.custom.yml logs app

# Common issues:
# 1. APP_KEY not set → Generate and add to .env.docker
# 2. DB connection failed → Check DB_PASSWORD matches
# 3. Port in use → Change port in docker-compose.custom.yml
```

### Database Connection Error

```bash
# Check database is running
docker-compose -f docker-compose.custom.yml ps db

# Check database logs
docker-compose -f docker-compose.custom.yml logs db

# Restart database
docker-compose -f docker-compose.custom.yml restart db
```

### Permission Errors

```bash
# Fix permissions
docker-compose -f docker-compose.custom.yml exec app chmod -R 775 storage bootstrap/cache
```

## Updating Firefly III

When new updates are available:

```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild with new code
docker-compose -f docker-compose.custom.yml build --no-cache app

# 3. Restart services
docker-compose -f docker-compose.custom.yml up -d

# The entrypoint script automatically runs:
# - Migrations
# - Database upgrades
# - Cache clearing
```

## Comparison: Custom vs Author's Docker Setup

| Feature | Author's Setup | Custom Setup |
|---------|---------------|--------------|
| **Source Code** | Pre-built image | Built from your code |
| **Customization** | Limited | Full control |
| **Modifications** | Not possible | Easy to modify |
| **Build Time** | None (pulls image) | 5-10 minutes first time |
| **Image Size** | Optimized | Optimized (multi-stage) |
| **Updates** | Pull new image | Rebuild from source |
| **Development** | Not suitable | Excellent |
| **Production** | Ready to go | Requires build |

## Best Practices

1. **Use .env.docker for secrets** - Never commit this file
2. **Regular backups** - Backup database and uploads
3. **Keep source updated** - Regularly pull updates
4. **Monitor logs** - Check for errors regularly
5. **Test before production** - Always test in local first
6. **Use strong passwords** - For DB_PASSWORD and tokens
7. **Enable HTTPS in production** - Use Nginx with SSL

## Advanced: Adding Custom Services

You can extend `docker-compose.custom.yml` with additional services:

```yaml
services:
  # ... existing services ...

  # Example: Add phpMyAdmin
  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    ports:
      - "8082:80"
    environment:
      PMA_HOST: db
    networks:
      - firefly

  # Example: Add monitoring
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    networks:
      - firefly
```

## Resources

- **Complete Documentation**: `docker/README.md` (in repo root)
- **Firefly III Docs**: https://docs.firefly-iii.org/
- **Docker Docs**: https://docs.docker.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/

## Summary

You now have a fully customizable Docker setup for Firefly III that:

✅ Builds from your source code
✅ Supports code modifications and rebuilds
✅ Includes both v1 and v2 frontend layouts
✅ Has PostgreSQL database with persistence
✅ Includes Data Importer for CSV imports
✅ Has automated cron jobs for recurring transactions
✅ Can be extended with additional services

**Next Steps:**
1. Make your desired code changes
2. Rebuild the container
3. Test your changes
4. Deploy to production (optional: add Nginx + SSL)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Compatible With:** Firefly III (Laravel 12 / PHP 8.4)
