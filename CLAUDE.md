# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Firefly III is a self-hosted personal finance manager built with Laravel (PHP) and features both Vue 2 (v1) and Alpine.js/Bootstrap (v2) frontends. It provides double-entry bookkeeping, budgets, recurring transactions, rule-based automation, and a comprehensive REST API.

**Tech Stack:**
- Backend: Laravel 12, PHP 8.4+
- Frontend: Dual layout system (v1: Vue 2, v2: Alpine.js + Vite)
- Database: MySQL/MariaDB, PostgreSQL, or SQLite
- Authentication: Laravel Passport (OAuth2), Sanctum, and optional remote user guard (for Authelia, etc.)
- Testing: PHPUnit with unit, integration, and feature test suites

## Development Commands

### PHP/Laravel

```bash
# Install dependencies
composer install

# Setup environment
cp .env.example .env
php artisan key:generate

# Database setup
php artisan migrate
php artisan db:seed  # If needed

# Laravel Passport OAuth keys (also runs automatically on composer update)
php artisan firefly-iii:laravel-passport-keys

# Clear caches
php artisan cache:clear
php artisan config:clear
php artisan route:clear
php artisan view:clear
php artisan twig:clean
```

### Testing

```bash
# Run all unit tests
composer unit-test
# Or: vendor/bin/phpunit -c phpunit.xml --testsuite unit --no-coverage

# Run all integration tests
composer integration-test
# Or: vendor/bin/phpunit -c phpunit.xml --testsuite integration --no-coverage

# Run tests with coverage
composer coverage
# Or: vendor/bin/phpunit -c phpunit.xml

# Run a single test file
vendor/bin/phpunit tests/unit/Path/To/TestFile.php

# Run a specific test method
vendor/bin/phpunit --filter testMethodName tests/unit/Path/To/TestFile.php
```

**Test Suites:**
- `tests/unit/` - Unit tests for isolated components
- `tests/integration/` - Integration tests for component interactions
- `tests/feature/` - Feature tests for full application flows

**Test Environment:** Uses SQLite with file-backed database at `storage/database/database.sqlite` (phpunit.xml:38-41, config/database.php:77-81)

### Frontend Development

**V1 Layout (Legacy - Vue 2 + Laravel Mix):**
```bash
# From repository root (using workspaces)
npm ci  # Install all dependencies
npm --workspace resources/assets/v1 run development  # Development build
npm --workspace resources/assets/v1 run watch        # Watch for changes
npm --workspace resources/assets/v1 run production   # Production build

# Or from within the v1 directory
cd resources/assets/v1
npm install
npm run development
```

**V2 Layout (Experimental - Alpine.js + Vite):**
```bash
# From repository root (using workspaces)
npm ci  # Install all dependencies
npm --workspace resources/assets/v2 run dev          # Development server
npm --workspace resources/assets/v2 run build        # Production build

# Or from within the v2 directory
cd resources/assets/v2
npm install
npm run dev
```

**Note:** The v2 layout is experimental. Use `FIREFLY_III_LAYOUT=v1` (default) or `FIREFLY_III_LAYOUT=v2` in `.env` to switch between layouts.

### Static Analysis

```bash
# PHPStan (static analysis)
vendor/bin/phpstan analyse

# Rector (automated refactoring)
vendor/bin/rector process --dry-run
```

### Artisan Commands

```bash
# Custom Firefly III commands
php artisan firefly-iii:upgrade-database
php artisan firefly-iii:verify-security-alerts
php artisan firefly-iii:correct-database  # For running balance feature

# List all Firefly III commands
php artisan list firefly-iii
```

## Architecture

### Core Domain Concepts

Firefly III is built around financial entities and double-entry bookkeeping:

1. **Accounts** (`app/Models/Account.php`) - The foundation of the system
   - Types: Asset, Expense, Revenue, Liability accounts (see `AccountType` model)
   - Managed by repository pattern (`app/Repositories/Account/`)

2. **Transactions** (`app/Models/Transaction.php`, `TransactionJournal.php`) - Financial movements
   - **TransactionJournal**: Groups related transactions (e.g., a transfer has two transactions)
   - **Transaction**: Individual debit/credit entries
   - Always balanced (double-entry): debits = credits

3. **Budgets** (`app/Models/Budget.php`) - Budget tracking and limits
   - `BudgetLimit` for time-based budget constraints
   - `AvailableBudget` for available amounts per period

4. **Categories** (`app/Models/Category.php`) - Transaction categorization

5. **Bills** (`app/Models/Bill.php`) - Recurring bill detection and tracking

6. **Piggy Banks** (`app/Models/PiggyBank.php`) - Savings goals

7. **Rules** (`app/Models/Rule.php`) - Transaction automation
   - Rule engine in `app/TransactionRules/`
   - Uses expression-based triggers and actions
   - Can auto-tag, categorize, set budgets, etc.

8. **Recurring Transactions** (`app/Models/Recurrence.php`) - Scheduled transactions

### Layered Architecture

```
routes/
├── web.php        # Web UI routes
├── api.php        # Authenticated API routes (OAuth2)
└── api-noauth.php # Public API routes

app/
├── Http/
│   ├── Controllers/     # MVC controllers for web UI
│   └── Requests/        # Form request validation
│
├── Api/
│   └── V1/             # API v1 controllers and resources
│
├── Models/             # Eloquent models (domain entities)
│
├── Repositories/       # Repository pattern for data access
│   ├── Account/
│   ├── Budget/
│   ├── Journal/        # Transaction journals
│   └── [etc...]
│
├── Services/           # Business logic services
│   ├── Internal/       # Internal services
│   ├── FireflyIIIOrg/  # External service integrations
│   ├── Password/
│   └── Webhook/
│
├── TransactionRules/   # Rule engine
│   ├── Engine/         # Rule execution engine
│   ├── Actions/        # Actions rules can perform
│   ├── Expressions/    # Rule expression language
│   └── Factory/
│
├── Transformers/       # API response transformers (Fractal)
│
├── Factory/            # Factory pattern for entity creation
│
├── Support/            # Helper classes and utilities
│
├── Validation/         # Custom validation rules
│
└── Jobs/              # Queued background jobs
```

### Key Patterns

**Repository Pattern:** Data access is abstracted through repositories (e.g., `AccountRepositoryInterface`). Repositories are bound in service providers (`app/Providers/`). Always use repositories, not direct Eloquent queries in controllers.

**Transformer Pattern:** API responses use Fractal transformers (`app/Transformers/`) to format data consistently.

**Factory Pattern:** Complex entity creation uses factories (`app/Factory/`) to handle validation and relationships.

**Rule Engine:** The transaction rule system (`app/TransactionRules/`) uses:
- `Engine/` - Processes rules against transactions
- `Expressions/` - Boolean expressions for matching conditions
- `Actions/` - Modifies transactions based on rules

### Database

- **Migrations:** Located in `database/migrations/`
- **Seeders:** Located in `database/seeders/`

**Note:** Models use Laravel's `HasFactory` trait, but concrete factory classes are not present in this repository. Test data creation is handled differently.

**Important:** Always create migrations for schema changes. Never modify existing migrations that have been released.

### Configuration

Configuration files are in `config/`:
- `firefly.php` - Main Firefly III configuration
- `database.php` - Database connections
- `auth.php` - Authentication guards and providers
- `.env.example` - Template for environment variables

**Note:** While `.env.example` mentions `_FILE` suffix support for Docker secrets, this is not implemented in the codebase itself. The app uses `envNonEmpty()` helper which returns defaults for empty values but does not read from files (bootstrap/app.php:50-57).

## Working with the API

The API follows JSON:API specification (partially) and uses:
- **Authentication:** OAuth2 (Laravel Passport) or personal access tokens (Sanctum) - routes use `auth:api,sanctum` middleware so either guard can authenticate (routes/api.php:719)
- **Routes:** Defined in `routes/api.php` (authenticated) and `routes/api-noauth.php` (public)
- **Controllers:** `app/Api/V1/Controllers/`
- **Transformers:** `app/Transformers/` (using Fractal library)
- **Validation:** Request classes in `app/Api/V1/Requests/`

API documentation: https://docs.firefly-iii.org/

## Frontend Structure

**V1 Layout:**
- Path: `resources/assets/v1/`
- Views: `resources/views/` (Twig templates via TwigBridge)
- Components: Vue 2 components in `resources/assets/v1/src/components/`
- Build: Laravel Mix (webpack wrapper)

**V2 Layout:**
- Path: `resources/assets/v2/`
- Views: Same Twig templates with v2-specific includes
- JavaScript: Alpine.js components; assets bundled with Vite
- Build: Vite for asset bundling (resources/assets/v2/package.json:5-8)
- Libraries: Bootstrap 5, Chart.js, AdminLTE theme

## Important Conventions

1. **Namespace Structure:**
   - `FireflyIII\` maps to `app/`
   - Tests use `Tests\` namespace

2. **Service Providers:** Auto-discovery is enabled. Register custom bindings in `app/Providers/`.

3. **Events & Listeners:** Located in `app/Events/` and `app/Listeners/`

4. **Validation:** Use Form Request classes for validation, not inline controller validation

5. **Enums:** PHP enums are used extensively (`app/Enums/`) for type safety

6. **Double-Entry Bookkeeping:** All transactions must balance. A transfer creates two Transaction records within one TransactionJournal.

7. **Multi-User Support:** Most queries are scoped to the authenticated user's "user group"

## Testing Guidelines

- Always run tests before committing: `composer unit-test && composer integration-test`
- Write unit tests for new repository methods and services
- Write integration tests for multi-component interactions
- Feature tests should test complete user workflows
- Mock external services in tests
- Create test data using appropriate methods (models use `HasFactory` but concrete factories are not implemented)

## Environment Variables

Key variables to set in `.env`:
- `APP_ENV=local` (for development)
- `APP_DEBUG=true` (for development)
- `DB_CONNECTION=mysql|pgsql|sqlite`
- `FIREFLY_III_LAYOUT=v1|v2` (select frontend version)
- `QUERY_PARSER_IMPLEMENTATION=new|legacy` (search query parser only - config/search.php:265; rule engine is separate)

See `.env.example` for complete list with documentation.

## Docker Setup

This project includes a Docker Compose setup in the `docker-setup/` directory for running Firefly III with all its components:

**Services:**
- `app` - Firefly III core application (port 80)
- `db` - PostgreSQL database
- `importer` - Firefly III Data Importer (port 81)
- `cron` - Automated cron jobs for recurring tasks

**Configuration Files:**
- `docker-compose.yml` - Full stack with app, database, importer, and cron
- `docker-compose-fireflyiii-only.yml` - Minimal setup (app and database only)
- `.env` - Firefly III environment variables
- `.db.env` - Database credentials
- `.importer.env` - Data Importer configuration

**Usage:**
```bash
cd docker-setup/

# Start all services
docker-compose up -d

# Start only Firefly III and database
docker-compose -f docker-compose-fireflyiii-only.yml up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

**Important Notes:**
- Firefly III will be available at `http://localhost` (port 80)
- Data Importer will be available at `http://localhost:81`
- The importer needs a Client ID from Firefly III (generate at `/profile` after registration)
- Set `STATIC_CRON_TOKEN` in `.env` to a 32-character random string for cron jobs
- The cron job runs daily at 3 AM to process recurring transactions
- Volumes persist data: `firefly_iii_upload` (attachments) and `firefly_iii_db` (database)

## Data Import

### Import Configurations (`import-configs/`)

This directory contains CSV import configuration files for the Firefly III Data Importer. These are JSON files that define:
- CSV column mappings to Firefly III transaction fields
- Date formats and delimiters
- Default accounts for imports
- Duplicate detection methods
- Custom tags for imported transactions

**Available Configurations:**
- `AIB_import_config_v1.json` - AIB bank statement imports
- `Revolut_import_config_v1.json`, `v2.json` - Revolut transaction exports
- `T212_import_config_v3.json`, `v4.json`, `v5.json` - Trading 212 statement imports

**Configuration Structure:**
- `roles` - Maps CSV columns to transaction fields (e.g., `date_transaction`, `description`, `amount`)
- `default_account` - Account ID to import transactions into
- `delimiter` - CSV delimiter (comma, semicolon, tab)
- `date` - Date format string
- `custom_tag` - Tag to add to all imported transactions
- `duplicate_detection_method` - How to detect duplicates (none, cell, row)

**Usage:**
1. Open the Data Importer at `http://localhost:81`
2. Upload a CSV file from `statements/`
3. Upload the corresponding import configuration JSON file
4. Review and confirm the import

### Bank Statements (`statements/`)

Contains CSV export files from various financial institutions for importing into Firefly III:
- `AIB_*.csv` - AIB bank statements
- `Revolut_*.csv` - Revolut transaction exports
- `T212_*.csv` - Trading 212 transaction history

**CSV Processing:**
- Each bank/service has a specific CSV format
- Import configurations are versioned to handle format changes
- Processed files (e.g., `*_processed.csv`) indicate manual cleanup or transformation

**Workflow:**
1. Export CSV from your bank/service
2. Save to `statements/` directory
3. Use matching configuration from `import-configs/`
4. Import via Data Importer web interface or API

## Common Gotchas

1. **Twig Caching:** Run `php artisan twig:clean` if Twig templates don't update
2. **Route Caching:** Always run `php artisan route:clear` after route changes in development
3. **Config Caching:** Run `php artisan config:clear` after changing config files
4. **Two Frontend Systems:** Remember v1 and v2 are separate build processes with different tech stacks
5. **Repository Bindings:** Repositories must be bound to interfaces in service providers
6. **Transaction Journals:** Always work with TransactionJournal, not Transaction directly, for creating/editing transactions
7. **Running Balance:** If enabling `USE_RUNNING_BALANCE=true`, must run `php artisan firefly-iii:correct-database`
8. **Docker Importer URL:** When using Docker, the Firefly III URL for the importer is `http://app:8080` (container hostname), not `localhost`
9. **Import Configurations:** Import config files are specific to CSV formats - bank format changes may require updating the configuration
