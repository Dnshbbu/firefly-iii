# Firefly III Setup Guide - Running Without Docker

Complete guide for setting up and running Firefly III directly on your VM/machine without using Docker containers.

## Prerequisites Check

Before starting, verify your system has:
- PHP 8.2+ (8.4 recommended)
- Composer (PHP package manager)
- Node.js 16+ and npm
- Database: MySQL 8.0+, PostgreSQL 13+, or SQLite 3.8+

## Step 1: Install Required Software

Since you're on WSL2 (Ubuntu/Debian-based), run these commands:

```bash
# Update package list
sudo apt update

# Install PHP 8.4+ with required extensions
sudo apt install -y php8.4 php8.4-cli php8.4-fpm php8.4-mysql php8.4-pgsql \
  php8.4-sqlite3 php8.4-curl php8.4-gd php8.4-mbstring php8.4-xml \
  php8.4-zip php8.4-bcmath php8.4-intl php8.4-ldap php8.4-soap

# If PHP 8.4 is not available, use PHP 8.3 or 8.2 (minimum 8.2 required)
# Just replace php8.4 with php8.3 or php8.2 in the above command

# Install Composer (PHP package manager)
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
sudo chmod +x /usr/local/bin/composer

# Install MySQL (or choose PostgreSQL/SQLite)
sudo apt install -y mysql-server mysql-client

# Start MySQL service
sudo service mysql start
```

### Alternative Database Options

**PostgreSQL:**
```bash
sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start
```

**SQLite:**
Already supported by PHP, no installation needed (simplest option for testing)

---

## Step 2: Configure Database

Choose one of the following based on your database preference:

### Option A: MySQL

```bash
# Secure MySQL installation (optional but recommended)
sudo mysql_secure_installation

# Create database and user
sudo mysql -e "CREATE DATABASE firefly;"
sudo mysql -e "CREATE USER 'firefly'@'localhost' IDENTIFIED BY 'your_secure_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON firefly.* TO 'firefly'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

### Option B: PostgreSQL

```bash
sudo service postgresql start
sudo -u postgres psql -c "CREATE DATABASE firefly;"
sudo -u postgres psql -c "CREATE USER firefly WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE firefly TO firefly;"
```

### Option C: SQLite (Easiest for Testing)

```bash
# Create database directory
mkdir -p storage/database
touch storage/database/database.sqlite
```

---

## Step 3: Configure Firefly III

```bash
# Navigate to project directory
cd /mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii

# Copy environment file
cp .env.example .env

# Install PHP dependencies
composer install --no-dev

# Generate application key
php artisan key:generate

# Generate OAuth2 keys for API
php artisan firefly-iii:laravel-passport-keys
```

### Edit Environment Configuration

Open the `.env` file:

```bash
nano .env  # or use your preferred editor: vim, code, etc.
```

**Key settings to configure:**

```ini
# Application settings
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8000

# For MySQL:
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=firefly
DB_USERNAME=firefly
DB_PASSWORD=your_secure_password

# OR for PostgreSQL:
# DB_CONNECTION=pgsql
# DB_HOST=127.0.0.1
# DB_PORT=5432
# DB_DATABASE=firefly
# DB_USERNAME=firefly
# DB_PASSWORD=your_secure_password

# OR for SQLite (simplest):
# DB_CONNECTION=sqlite
# DB_DATABASE=/mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii/storage/database/database.sqlite

# Choose frontend version (v1 is stable, v2 is experimental)
FIREFLY_III_LAYOUT=v1

# Set this to a random 32-character string for security
STATIC_CRON_TOKEN=your_random_32_character_string_here

# Optional: Set your timezone
TZ=Europe/Dublin
```

**Generate a secure token:**
```bash
# Generate random 32-character string for STATIC_CRON_TOKEN
openssl rand -base64 32
```

---

## Step 4: Run Database Migrations

```bash
# Run migrations to create database tables
php artisan migrate --seed

# Clear all caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

**Note:** The `--seed` flag is optional. It seeds the database with initial data if needed.

---

## Step 5: Build Frontend Assets

### For V1 Layout (Recommended - Stable)

```bash
# Install all npm dependencies (from project root)
npm ci

# Build frontend assets for v1
npm --workspace resources/assets/v1 run production
```

**For development with hot reload:**
```bash
npm --workspace resources/assets/v1 run watch
```

### For V2 Layout (Experimental)

```bash
# Install dependencies
npm ci

# Build frontend assets for v2
npm --workspace resources/assets/v2 run build
```

**For development server:**
```bash
npm --workspace resources/assets/v2 run dev
```

---

## Step 6: Set Proper Permissions

```bash
# Set storage and cache permissions
chmod -R 775 storage bootstrap/cache

# If you encounter permission issues, set ownership
sudo chown -R $USER:$USER storage bootstrap/cache
```

---

## Step 7: Run the Application

You have two options for running Firefly III:

### Option A: PHP Built-in Server (Quick Start - Development)

**Easiest way to get started:**

```bash
php artisan serve
```

This will start the server at `http://localhost:8000`

**Custom host and port:**
```bash
php artisan serve --host=0.0.0.0 --port=8080
```

### Option B: Nginx + PHP-FPM (Production-like Setup)

For a more production-ready setup:

1. **Install Nginx:**
```bash
sudo apt install -y nginx
```

2. **Create Nginx configuration:**
```bash
sudo nano /etc/nginx/sites-available/firefly
```

3. **Add this configuration:**
```nginx
server {
    listen 80;
    server_name localhost;
    root /mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii/public;

    index index.php index.html;

    # Prevent access to hidden files
    location ~ /\. {
        deny all;
    }

    # Main location block
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # PHP-FPM configuration
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.4-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # Deny access to .htaccess files
    location ~ /\.ht {
        deny all;
    }
}
```

4. **Enable the site and restart services:**
```bash
# Test nginx configuration
sudo nginx -t

# Enable the site
sudo ln -s /etc/nginx/sites-available/firefly /etc/nginx/sites-enabled/

# Disable default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Start services
sudo service php8.4-fpm start
sudo service nginx restart
```

---

## Step 8: Access Firefly III

Open your browser and navigate to:

- **PHP built-in server:** `http://localhost:8000`
- **Nginx:** `http://localhost`

You should see the Firefly III registration page. Create your first account!

**Default Admin Setup:**
- Register your first user account
- This becomes the admin account
- No default credentials - you create them during registration

---

## Step 9: Setup Cron Jobs (Optional - For Recurring Transactions)

Firefly III needs a cron job to process recurring transactions, check for bill updates, and other scheduled tasks.

```bash
# Edit crontab
crontab -e

# Add this line (runs every minute):
* * * * * cd /mnt/c/Users/StdUser/Desktop/MyProjects/firefly-iii && php artisan schedule:run >> /dev/null 2>&1
```

**Verify cron is running:**
```bash
# Check if cron service is active
sudo service cron status

# Start cron if not running
sudo service cron start
```

---

## Quick Reference Commands

### Daily Operations

```bash
# Start database
sudo service mysql start      # For MySQL
sudo service postgresql start # For PostgreSQL

# Start Firefly III (development)
php artisan serve

# Access: http://localhost:8000
```

### Cache Management

```bash
# Clear all caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
php artisan twig:clean
```

### Asset Rebuilding

```bash
# Rebuild frontend assets (v1)
npm --workspace resources/assets/v1 run production

# Rebuild frontend assets (v2)
npm --workspace resources/assets/v2 run build
```

### Database Operations

```bash
# Run pending migrations
php artisan migrate

# Rollback last migration
php artisan migrate:rollback

# Fresh database (WARNING: deletes all data)
php artisan migrate:fresh --seed

# Upgrade database (after version updates)
php artisan firefly-iii:upgrade-database
```

---

## Troubleshooting

### Permission Errors

```bash
# Fix storage permissions
sudo chown -R $USER:$USER storage bootstrap/cache
chmod -R 775 storage bootstrap/cache
```

### Database Connection Issues

```bash
# Verify database is running
sudo service mysql status      # MySQL
sudo service postgresql status # PostgreSQL

# Test database connection
php artisan tinker
# Then run: DB::connection()->getPdo();
```

### Migration Failures

```bash
# Clear config cache and retry
php artisan config:clear
php artisan cache:clear

# Try migration again
php artisan migrate

# If still failing, fresh install (WARNING: deletes data)
php artisan migrate:fresh --seed
```

### Frontend Assets Not Loading

```bash
# Reinstall npm dependencies
rm -rf node_modules package-lock.json
npm install

# Rebuild assets
npm ci
npm --workspace resources/assets/v1 run production

# Clear Laravel caches
php artisan cache:clear
php artisan view:clear
```

### "Key length too long" Error (MySQL)

Edit `config/database.php` and add to MySQL configuration:
```php
'charset' => 'utf8mb4',
'collation' => 'utf8mb4_unicode_ci',
'engine' => 'InnoDB ROW_FORMAT=DYNAMIC',
```

Then run:
```bash
php artisan config:clear
php artisan migrate:fresh
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
php artisan serve --port=8080
```

### PHP Extensions Missing

```bash
# Check loaded extensions
php -m

# Install missing extension (example for bcmath)
sudo apt install php8.4-bcmath

# Restart PHP-FPM if using Nginx
sudo service php8.4-fpm restart
```

---

## Performance Optimization

### Enable OpCache (Production)

Edit PHP configuration:
```bash
sudo nano /etc/php/8.4/fpm/php.ini
```

Enable OpCache:
```ini
opcache.enable=1
opcache.memory_consumption=128
opcache.max_accelerated_files=10000
opcache.revalidate_freq=2
```

Restart PHP-FPM:
```bash
sudo service php8.4-fpm restart
```

### Configure Laravel for Production

Edit `.env`:
```ini
APP_ENV=production
APP_DEBUG=false

# Cache configuration
CACHE_DRIVER=file
SESSION_DRIVER=file
QUEUE_CONNECTION=sync
```

Cache configuration files:
```bash
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

---

## Updating Firefly III

When pulling new updates from git:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
composer install --no-dev
npm ci

# Rebuild assets
npm --workspace resources/assets/v1 run production

# Run migrations
php artisan migrate

# Upgrade database
php artisan firefly-iii:upgrade-database

# Clear caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
```

---

## Security Checklist

- [ ] Change `APP_KEY` (generated by `php artisan key:generate`)
- [ ] Set strong database password
- [ ] Generate random `STATIC_CRON_TOKEN` (32 characters)
- [ ] Set `APP_DEBUG=false` in production
- [ ] Use HTTPS in production (configure in Nginx with SSL certificate)
- [ ] Keep PHP and dependencies updated
- [ ] Restrict file permissions (755 for directories, 644 for files)
- [ ] Enable firewall (ufw) and only allow necessary ports

---

## Additional Resources

- **Official Documentation:** https://docs.firefly-iii.org/
- **API Documentation:** https://docs.firefly-iii.org/references/api/
- **GitHub Repository:** https://github.com/firefly-iii/firefly-iii
- **Community Forum:** https://gitter.im/firefly-iii/firefly-iii

---

## Next Steps

After successfully running Firefly III:

1. **Complete your profile** - Set up your name, email, and preferences
2. **Create accounts** - Add your bank accounts, credit cards, etc.
3. **Import transactions** - Use the CSV preprocessor in `pythondashboard/` (see [pythondashboard/README.md](../README.md))
4. **Set up budgets** - Create monthly budgets for expense categories
5. **Create rules** - Automate transaction categorization
6. **Explore the API** - Generate OAuth tokens at `/profile` for API access

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Firefly III Version:** Compatible with Laravel 12 / PHP 8.4
