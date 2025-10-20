#!/bin/bash
set -e

echo "========================================"
echo "Firefly III Container Starting..."
echo "========================================"

# Wait for database to be ready
echo "Waiting for database connection..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if php -r "
        try {
            \$pdo = new PDO(
                'pgsql:host=${DB_HOST};port=${DB_PORT};dbname=${DB_DATABASE}',
                '${DB_USERNAME}',
                '${DB_PASSWORD}'
            );
            exit(0);
        } catch (Exception \$e) {
            exit(1);
        }
    "; then
        echo "✓ Database connection established"
        break
    fi

    attempt=$((attempt + 1))
    echo "Waiting for database... (${attempt}/${max_attempts})"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ Failed to connect to database after ${max_attempts} attempts"
    exit 1
fi

# Generate APP_KEY if not set
if [ -z "$APP_KEY" ] || [ "$APP_KEY" = "SomeRandomStringOf32CharsExactly" ]; then
    echo "========================================"
    echo "WARNING: APP_KEY not set or using default!"
    echo "Generating new APP_KEY..."
    echo "========================================"
    php artisan key:generate --force
fi

# Create storage directories if they don't exist
echo "Setting up storage directories..."
mkdir -p storage/framework/cache/data
mkdir -p storage/framework/sessions
mkdir -p storage/framework/views
mkdir -p storage/logs
mkdir -p storage/upload
mkdir -p storage/database
mkdir -p bootstrap/cache

# Set proper permissions
echo "Setting permissions..."
chmod -R 775 storage bootstrap/cache 2>/dev/null || true

# Clear caches
echo "Clearing application caches..."
php artisan config:clear
php artisan cache:clear
php artisan route:clear
php artisan view:clear

# Generate OAuth keys if they don't exist
if [ ! -f "storage/oauth-private.key" ]; then
    echo "Generating OAuth2 keys..."
    php artisan firefly-iii:laravel-passport-keys
fi

# Run database migrations
echo "Running database migrations..."
php artisan migrate --force --no-interaction

# Upgrade database (for updates)
echo "Running database upgrade..."
php artisan firefly-iii:upgrade-database --force

# Verify security alerts
echo "Checking for security alerts..."
php artisan firefly-iii:verify-security-alerts || true

# Cache configuration for better performance
if [ "$APP_ENV" = "production" ]; then
    echo "Caching configuration for production..."
    php artisan config:cache
    php artisan route:cache
    php artisan view:cache
fi

echo "========================================"
echo "✓ Firefly III started successfully!"
echo "Frontend Layout: ${FIREFLY_III_LAYOUT:-v1}"
echo "Environment: ${APP_ENV:-production}"
echo "Debug Mode: ${APP_DEBUG:-false}"
echo "========================================"

# Execute the main command (usually php-fpm)
exec "$@"
