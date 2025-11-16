# Contact Data Enrichment System
A simple Celery implementation to leverage Async tasks. This project focuses on the idea where a request is offloaded to be fulfilled by another service.

Here a scalable contact enrichment pipeline is built with Django and Celery that processes CSV files containing contact information and enriches them with email validation and company data.

## 📋 Overview

This system allows you to:
- Upload CSV files with contact information (Sync)
- Automatically validate email addresses (Async)
- Enrich company information (domain, size, location) (Async)
- Track processing status and results
- Scale horizontally for high-volume processing

## 🏗️ Architecture & Design Patterns

### Master/Worker Pattern (Orchestrator/Worker)

This project implements a **Master/Worker** pattern for distributed data processing tasks.

```
┌─────────────────────────────────────────────────────────────┐
│                    MASTER/ORCHESTRATOR                      │
│              process_csv_create_batch                       │
│                                                             │
│  • Reads CSV file                                           │
│  • Splits into batches (2 contacts per batch)               │
│  • Spawns parallel worker tasks                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌────────┐   ┌────────┐   ┌────────┐
    │WORKER 1│   │WORKER 2│   │WORKER N│
    │Batch 0 │   │Batch 1 │   │Batch N │
    │        │   │        │   │        │
    │• Email │   │• Email │   │• Email │
    │  Valid │   │  Valid │   │  Valid │
    │• Enrich│   │• Enrich│   │• Enrich│
    └────┬───┘   └────┬───┘   └────┬───┘
         │            │            │
         └────────────┼────────────┘
                      ▼
         ┌────────────────────────┐
         │      AGGREGATOR        │
         │ aggregate_batch_results│
         │                        │
         │ • Collect all results  │
         │ • Calculate totals     │
         │ • Update job status    │
         └────────────────────────┘
```

### Pattern Components

#### 1. **Master Task** (`process_csv_create_batch`)
- **Queue**: `default`
- **Responsibility**: Orchestration
- Reads CSV and divides work into batches
- Creates database records for tracking
- Spawns multiple worker tasks using Celery's `chord()`
- Coordinates final aggregation

#### 2. **Worker Tasks** (`process_contact_batch_data`)
- **Queue**: `batch_processing`
- **Responsibility**: Parallel execution
- Processes one batch (2 contacts can be extended) independently
- Validates emails using external service
- Enriches company data
- Returns results for aggregation
- **Scalability**: Multiple workers can run in parallel

#### 3. **Aggregator Task** (`aggregate_batch_results`)
- **Queue**: `default`
- **Responsibility**: Result collection
- Waits for all workers to complete
- Aggregates success/failure counts
- Updates final job status

## 🛠️ Tech Stack

- **Backend**: Django 5.1 + Django Ninja
- **Task Queue**: Celery 5.4
- **Message Broker**: Redis 7 (in-memory queue)
- **Database**: PostgreSQL 17
- **Monitoring**: Flower (Celery monitoring tool)
- **Containerization**: Docker + Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- `.env` file with required environment variables

### Environment Setup

Create a `.env` file in the project root:
```env
DJANGO_SECRET_KEY=your-secret-key-here
```

### Run the Application

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| **Django API** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Flower** | http://localhost:5555 | Celery monitoring dashboard |
| **PostgreSQL** | localhost:5433 | Database |
| **Redis** | localhost:6379 | Message broker |


## 📄 CSV Format

Your CSV file should have the following columns:

```csv
first_name,last_name,email,company
John,Doe,john@example.com,Acme Corp
Jane,Smith,jane@techco.com,TechCo Inc
```

## 📊 Monitoring with Flower

Access Flower at http://localhost:5555 to monitor:
- Active tasks
- Task success/failure rates
- Worker status and availability
- Task execution times
- Queue lengths

### Database Migrations
```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

## 🔍 How Celery Discovers Tasks

1. **Django Initialization** (`backend/__init__.py`)
   ```python
   from .celery_app import app as celery_app
   ```

2. **Celery Autodiscovery** (`backend/celery_app.py`)
   ```python
   app.autodiscover_tasks(lambda: ['apps.rest'])
   ```

3. **Task Registration** (`backend/apps/rest/tasks.py`)
   ```python
   @shared_task
   def process_csv_create_batch(self, job_id, file_name):
       # Task logic
   ```

4. **Worker Startup**
   - Worker imports Django project
   - Celery autodiscovery finds `tasks.py`
   - All `@shared_task` functions are registered
   - Worker polls queue and executes tasks