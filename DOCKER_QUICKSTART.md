# Firefly III Custom Docker - Quick Start

**TL;DR**: Build Firefly III from source with full customization support.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Setup (5 Minutes)

```bash
# 1. Configure environment
cp .env.docker.example .env.docker

# 2. Generate secrets
echo "APP_KEY=$(openssl rand -base64 32)"
echo "STATIC_CRON_TOKEN=$(openssl rand -hex 16)"

# 3. Edit .env.docker with generated values
nano .env.docker
# Set: APP_KEY, DB_PASSWORD, STATIC_CRON_TOKEN, SITE_OWNER

# 4. Build and start
docker-compose -f docker-compose.custom.yml build
docker-compose -f docker-compose.custom.yml up -d

# 5. Access
# Firefly III: http://localhost:8080
# Data Importer: http://localhost:8081
```

## Daily Commands

```bash
# Start services
docker-compose -f docker-compose.custom.yml up -d

# Stop services
docker-compose -f docker-compose.custom.yml down

# View logs
docker-compose -f docker-compose.custom.yml logs -f app

# Access container shell
docker-compose -f docker-compose.custom.yml exec app bash
```

## Making Code Changes

```bash
# Method 1: Rebuild after changes
docker-compose -f docker-compose.custom.yml up -d --build app

# Method 2: Development mode
# Uncomment volume mount in docker-compose.custom.yml:
#   volumes:
#     - ./:/var/www/html:cached
docker-compose -f docker-compose.custom.yml restart app
```

## Useful Commands

```bash
# Clear caches
docker-compose -f docker-compose.custom.yml exec app php artisan cache:clear

# Run migrations
docker-compose -f docker-compose.custom.yml exec app php artisan migrate

# Backup database
docker-compose -f docker-compose.custom.yml exec db pg_dump -U firefly firefly > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.custom.yml exec -T db psql -U firefly firefly

# View database
docker-compose -f docker-compose.custom.yml exec db psql -U firefly -d firefly
```

## Troubleshooting

```bash
# Rebuild without cache
docker-compose -f docker-compose.custom.yml build --no-cache app

# Check service status
docker-compose -f docker-compose.custom.yml ps

# Restart everything
docker-compose -f docker-compose.custom.yml restart

# Nuclear option (deletes all data!)
docker-compose -f docker-compose.custom.yml down -v
```

## File Structure

```
firefly-iii/
├── Dockerfile                    # Multi-stage build
├── docker-compose.custom.yml     # Your compose file
├── .env.docker.example          # Template (copy to .env.docker)
├── .env.docker                   # Your config (git ignored)
└── docker/
    ├── README.md                # Detailed docs
    ├── entrypoint.sh            # Startup script
    ├── php.ini                  # PHP config
    └── nginx.conf               # Nginx config (optional)
```

## Documentation

- **Detailed Guide**: `docker/README.md`
- **Build Tutorial**: `pythondashboard/Docs/DOCKER_BUILD_GUIDE.md`
- **VM Setup**: `pythondashboard/Docs/FIREFLY_SETUP_GUIDE.md`

## Architecture

- **app**: Firefly III (PHP 8.4-FPM) - Built from source
- **db**: PostgreSQL 16 - Database
- **importer**: Data Importer - CSV imports
- **cron**: Alpine - Scheduled tasks

## Switch Frontend Layout

```bash
# Edit .env.docker
FIREFLY_III_LAYOUT=v2  # or v1

# Restart
docker-compose -f docker-compose.custom.yml restart app
```

## Enable Redis Cache

```bash
# 1. Uncomment redis service in docker-compose.custom.yml

# 2. Edit .env.docker:
CACHE_DRIVER=redis
SESSION_DRIVER=redis
REDIS_HOST=redis

# 3. Restart
docker-compose -f docker-compose.custom.yml up -d
```

## Important Notes

⚠️ **First time setup takes 5-10 minutes** to build all assets
⚠️ **Always backup before updates**: Database and uploads
⚠️ **Never commit .env.docker**: Contains secrets
✅ **Both v1 and v2 frontends**: Built into image
✅ **Auto migrations**: Runs on container start
✅ **Source modifications**: Rebuild to apply

## Quick Links

- Firefly III: http://localhost:8080
- Data Importer: http://localhost:8081
- Official Docs: https://docs.firefly-iii.org/
- GitHub: https://github.com/firefly-iii/firefly-iii
