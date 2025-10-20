# Multi-stage Dockerfile for Firefly III
# This Dockerfile builds Firefly III from source with both v1 and v2 frontend assets
# Optimized for production use with minimal image size

###############################################################################
# Stage 1: Build Frontend Assets
###############################################################################
FROM node:22-alpine AS frontend-builder

WORKDIR /build

# Copy package files
COPY package*.json ./
COPY resources/assets/v1/package*.json ./resources/assets/v1/
COPY resources/assets/v2/package*.json ./resources/assets/v2/

# Install dependencies
RUN npm ci --ignore-scripts

# Copy frontend source code
COPY resources/assets ./resources/assets

# Build v1 assets (stable version)
# Note: v2 build can be added later if needed
RUN npm --workspace resources/assets/v1 run production

###############################################################################
# Stage 2: Install PHP Dependencies
###############################################################################
FROM composer:2 AS composer-builder

WORKDIR /build

# Copy composer files
COPY composer.json composer.lock ./

# Install PHP dependencies (no dev dependencies for production)
# Use --ignore-platform-reqs since extensions will be available in final stage
RUN composer install \
    --no-dev \
    --no-interaction \
    --no-progress \
    --no-scripts \
    --prefer-dist \
    --optimize-autoloader \
    --ignore-platform-reqs

###############################################################################
# Stage 3: Production Runtime Image
###############################################################################
FROM php:8.4-fpm-alpine

LABEL maintainer="Custom Firefly III Build"
LABEL description="Firefly III Personal Finance Manager - Built from Source"

# Set working directory
WORKDIR /var/www/html

# Install system dependencies and PHP extensions
RUN apk add --no-cache \
    # System utilities
    bash \
    curl \
    git \
    tzdata \
    # Image processing
    freetype \
    libjpeg-turbo \
    libpng \
    # Database drivers
    postgresql-dev \
    # Other dependencies
    icu-dev \
    libzip-dev \
    libxml2-dev \
    oniguruma-dev \
    openldap-dev \
    # Build dependencies (temporary)
    $PHPIZE_DEPS \
    freetype-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    && \
    # Configure and install PHP extensions
    docker-php-ext-configure gd \
        --with-freetype \
        --with-jpeg && \
    docker-php-ext-install -j$(nproc) \
        bcmath \
        gd \
        intl \
        ldap \
        mysqli \
        pdo_mysql \
        pdo_pgsql \
        pgsql \
        soap \
        zip && \
    # Install additional extensions
    pecl install redis && \
    docker-php-ext-enable redis && \
    # Clean up build dependencies
    apk del --no-network $PHPIZE_DEPS \
        freetype-dev \
        libjpeg-turbo-dev \
        libpng-dev && \
    rm -rf /tmp/* /var/cache/apk/*

# Copy custom PHP configuration
COPY docker/php.ini /usr/local/etc/php/conf.d/firefly.ini

# Copy application code
COPY --chown=www-data:www-data . /var/www/html

# Copy built frontend assets from frontend-builder stage
COPY --from=frontend-builder --chown=www-data:www-data /build/public /var/www/html/public

# Copy vendor dependencies from composer-builder stage
COPY --from=composer-builder --chown=www-data:www-data /build/vendor /var/www/html/vendor

# Create necessary directories and set permissions
RUN mkdir -p \
    storage/framework/cache/data \
    storage/framework/sessions \
    storage/framework/views \
    storage/logs \
    storage/upload \
    storage/database \
    bootstrap/cache && \
    chown -R www-data:www-data storage bootstrap/cache && \
    chmod -R 775 storage bootstrap/cache

# Copy entrypoint script
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose port 8080 (PHP-FPM will listen on port 9000)
EXPOSE 8080

# Switch to www-data user for security
USER www-data

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["php-fpm"]
