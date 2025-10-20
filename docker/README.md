# Custom Docker Setup for Firefly III

This directory contains the custom Docker configuration files for building and running Firefly III from source code.

## Overview

This custom Docker setup allows you to:
- Build Firefly III directly from your modified source code
- Customize any part of the application
- Run a complete stack with database, importer, and cron jobs
- Switch between v1 and v2 frontend layouts
- Easily rebuild after making code changes

## Architecture

### Services

1. **app** - Firefly III application (built from source)
   - PHP 8.4-FPM
   - Both v1 and v2 frontend assets built-in
   - Automatic migrations on startup
   - Port: 8080

2. **db** - PostgreSQL 16 database
   - Persistent data storage
   - Health checks enabled
   - Automatic backups via volumes

3. **importer** - Data Importer service
   - Official Firefly III Data Importer image
   - CSV import functionality
   - Port: 8081

4. **cron** - Scheduled tasks
   - Daily cron job at 3 AM
   - Recurring transactions processing
   - Bill matching and updates

### Optional Services

- **nginx** - Reverse proxy (commented out by default)
- **redis** - Cache and session storage (commented out by default)

## Quick Start Guide

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 2GB free disk space
- 1GB RAM minimum (2GB recommended)

### Step 1: Configure Environment

```bash
# Copy the example environment file
cp .env.docker.example .env.docker

# Generate APP_KEY
openssl rand -base64 32

# Generate STATIC_CRON_TOKEN
openssl rand -hex 16

# Edit .env.docker and set:
# - APP_KEY (32 characters)
# - DB_PASSWORD (strong password)
# - STATIC_CRON_TOKEN (32 characters)
# - SITE_OWNER (your email)
# - APP_URL (your domain or http://localhost:8080)
nano .env.docker
```

### Step 2: Build and Start

```bash
# Build the application image (first time only, ~5-10 minutes)
docker-compose -f docker-compose.custom.yml build

# Start all services
docker-compose -f docker-compose.custom.yml up -d

# View logs
docker-compose -f docker-compose.custom.yml logs -f app
```

### Step 3: Access Firefly III

Open your browser and navigate to:
- **Firefly III**: http://localhost:8080
- **Data Importer**: http://localhost:8081

Create your first account (this becomes the admin account).

### Step 4: Setup Data Importer

1. Log into Firefly III at http://localhost:8080
2. Go to **Options** → **Profile** → **OAuth**
3. Create a new **Personal Access Token**
4. Copy the token
5. Add it to `.env.docker`:
   ```bash
   FIREFLY_III_ACCESS_TOKEN=your_generated_token_here
   ```
6. Restart the importer:
   ```bash
   docker-compose -f docker-compose.custom.yml restart importer
   ```

## Daily Usage

### Starting and Stopping

```bash
# Start all services
docker-compose -f docker-compose.custom.yml up -d

# Stop all services
docker-compose -f docker-compose.custom.yml down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose -f docker-compose.custom.yml down -v
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.custom.yml logs -f

# Specific service
docker-compose -f docker-compose.custom.yml logs -f app
docker-compose -f docker-compose.custom.yml logs -f db
docker-compose -f docker-compose.custom.yml logs -f cron
```

### Accessing the Container

```bash
# Open bash shell in app container
docker-compose -f docker-compose.custom.yml exec app bash

# Run artisan commands
docker-compose -f docker-compose.custom.yml exec app php artisan cache:clear
docker-compose -f docker-compose.custom.yml exec app php artisan migrate
```

## Making Code Changes

When you modify the source code, you need to rebuild the application container:

```bash
# Stop the app service
docker-compose -f docker-compose.custom.yml stop app

# Rebuild the image
docker-compose -f docker-compose.custom.yml build app

# Start the app service
docker-compose -f docker-compose.custom.yml up -d app

# Or do it all in one command:
docker-compose -f docker-compose.custom.yml up -d --build app
```

### Development Mode

For active development, you can mount your source code directly:

1. Edit `docker-compose.custom.yml`
2. Uncomment the volume mount under the `app` service:
   ```yaml
   volumes:
     - ./:/var/www/html:cached
   ```
3. Restart: `docker-compose -f docker-compose.custom.yml restart app`

**Note**: You'll need to manually run frontend builds when in development mode:
```bash
docker-compose -f docker-compose.custom.yml exec app bash
npm --workspace resources/assets/v1 run watch
```

## Switching Frontend Layouts

To switch between v1 (stable) and v2 (experimental) layouts:

1. Edit `.env.docker`:
   ```bash
   FIREFLY_III_LAYOUT=v2  # or v1
   ```

2. Restart the app:
   ```bash
   docker-compose -f docker-compose.custom.yml restart app
   ```

3. Clear your browser cache

## Database Management

### Backup Database

```bash
# Backup PostgreSQL database
docker-compose -f docker-compose.custom.yml exec db pg_dump -U firefly firefly > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Restore from backup
cat backup_20250101.sql | docker-compose -f docker-compose.custom.yml exec -T db psql -U firefly firefly
```

### Access Database Shell

```bash
# PostgreSQL shell
docker-compose -f docker-compose.custom.yml exec db psql -U firefly -d firefly
```

### Reset Database

```bash
# WARNING: This deletes all data!
docker-compose -f docker-compose.custom.yml exec app php artisan migrate:fresh --seed
```

## Performance Optimization

### Enable Redis Cache

1. Uncomment the `redis` service in `docker-compose.custom.yml`
2. Edit `.env.docker`:
   ```bash
   CACHE_DRIVER=redis
   SESSION_DRIVER=redis
   REDIS_HOST=redis
   ```
3. Restart: `docker-compose -f docker-compose.custom.yml up -d`

### Enable Nginx Reverse Proxy

1. Uncomment the `nginx` service in `docker-compose.custom.yml`
2. Adjust ports (nginx will use port 80)
3. Restart: `docker-compose -f docker-compose.custom.yml up -d`

### Production Optimizations

In `.env.docker`, set:
```bash
APP_ENV=production
APP_DEBUG=false
CACHE_DRIVER=redis
SESSION_DRIVER=redis
```

Run optimization commands:
```bash
docker-compose -f docker-compose.custom.yml exec app php artisan config:cache
docker-compose -f docker-compose.custom.yml exec app php artisan route:cache
docker-compose -f docker-compose.custom.yml exec app php artisan view:cache
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.custom.yml logs app

# Common issues:
# 1. APP_KEY not set or invalid
# 2. Database connection failed
# 3. Permission issues
```

### Database Connection Error

```bash
# Check if database is running
docker-compose -f docker-compose.custom.yml ps db

# Check database logs
docker-compose -f docker-compose.custom.yml logs db

# Verify credentials in .env.docker match
```

### Frontend Assets Not Loading

```bash
# Rebuild with no cache
docker-compose -f docker-compose.custom.yml build --no-cache app

# Or manually rebuild assets
docker-compose -f docker-compose.custom.yml exec app bash
npm ci
npm --workspace resources/assets/v1 run production
```

### Permission Denied Errors

```bash
# Fix permissions in container
docker-compose -f docker-compose.custom.yml exec app chmod -R 775 storage bootstrap/cache
```

### Cron Job Not Running

```bash
# Check cron logs
docker-compose -f docker-compose.custom.yml logs cron

# Verify STATIC_CRON_TOKEN is set correctly in .env.docker
# Ensure it's exactly 32 characters

# Test cron URL manually
docker-compose -f docker-compose.custom.yml exec cron wget -qO- http://app:8080/api/v1/cron/YOUR_TOKEN
```

### Port Already in Use

```bash
# Change ports in docker-compose.custom.yml
ports:
  - "8090:8080"  # Change 8080 to 8090 or any available port
```

## Maintenance Commands

```bash
# Clear all caches
docker-compose -f docker-compose.custom.yml exec app php artisan cache:clear
docker-compose -f docker-compose.custom.yml exec app php artisan config:clear
docker-compose -f docker-compose.custom.yml exec app php artisan route:clear
docker-compose -f docker-compose.custom.yml exec app php artisan view:clear

# Run migrations
docker-compose -f docker-compose.custom.yml exec app php artisan migrate

# Upgrade database (after updates)
docker-compose -f docker-compose.custom.yml exec app php artisan firefly-iii:upgrade-database

# Check for security alerts
docker-compose -f docker-compose.custom.yml exec app php artisan firefly-iii:verify-security-alerts

# Generate new OAuth keys
docker-compose -f docker-compose.custom.yml exec app php artisan firefly-iii:laravel-passport-keys
```

## Updating Firefly III

When you pull new changes from git:

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.custom.yml up -d --build app

# The entrypoint script will automatically:
# - Run migrations
# - Upgrade database
# - Clear caches
```

## Security Considerations

1. **Change default passwords**: Never use default values for `DB_PASSWORD`
2. **Generate secure tokens**: Use strong random values for `APP_KEY` and `STATIC_CRON_TOKEN`
3. **Use HTTPS in production**: Configure SSL certificates with Nginx
4. **Disable debug mode**: Set `APP_DEBUG=false` in production
5. **Regular backups**: Backup database and uploads regularly
6. **Keep updated**: Regularly pull updates and rebuild

## Advanced Configuration

### Custom PHP Settings

Edit `docker/php.ini` to customize PHP configuration:
- Memory limits
- Upload sizes
- Timeouts
- OPcache settings

Rebuild after changes:
```bash
docker-compose -f docker-compose.custom.yml up -d --build app
```

### Custom Nginx Configuration

Edit `docker/nginx.conf` to customize Nginx:
- SSL certificates
- Cache headers
- Compression settings
- Security headers

### Environment Variables

All Firefly III environment variables can be set in `.env.docker`. See `.env.docker.example` for all available options.

## File Structure

```
firefly-iii/
├── Dockerfile                      # Multi-stage build definition
├── docker-compose.custom.yml       # Docker Compose configuration
├── .dockerignore                   # Files excluded from build
├── .env.docker.example            # Environment template
├── .env.docker                     # Your environment (not in git)
└── docker/                        # Configuration files
    ├── README.md                  # This file
    ├── entrypoint.sh              # Container startup script
    ├── php.ini                    # PHP configuration
    └── nginx.conf                 # Nginx configuration (optional)
```

## Getting Help

- **Official Docs**: https://docs.firefly-iii.org/
- **GitHub Issues**: https://github.com/firefly-iii/firefly-iii/issues
- **Community**: https://gitter.im/firefly-iii/firefly-iii

## License

Firefly III is licensed under the AGPL-3.0-or-later license.
