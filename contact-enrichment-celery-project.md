# Contact Enrichment Pipeline - Simple Overview

## Data

### Contact Model
Stores individual contact information and enrichment results:
- **Original Data**: name, email, company, phone
- **Enriched Data**: email_valid, company_domain, company_size, location
- **Tracking**: job_id, batch_id, status (pending/processing/success/failed), error_message, processed_at

### Job Model
Tracks overall CSV processing job:
- **Identifiers**: id, filename
- **Status**: status, total_count, success_count, failed_count
- **Timestamps**: started_at, completed_at

---

## Architecture

```
User → Django API → Redis Queue → Celery Workers → Database
                                        ↓
                                  External APIs
                                  (Email Validator,
                                   Company Enricher)
```

### Components
- **Django API**: Handles CSV upload, creates jobs, returns status
- **Redis**: Message broker for task queue
- **Celery Workers**: Process contacts in parallel batches
- **PostgreSQL**: Stores contacts and job results
- **Mock APIs**: Simulate email validation and company enrichment services

---

## Flow: Upload to Workers to Report

### 1. Upload Phase
1. User uploads CSV file via `POST /jobs/upload`
2. Django creates a Job record
3. Django triggers parent Celery task `process_csv_file(job_id, file_path)`

### 2. Task Distribution
1. Parent task reads CSV and creates Contact records (status = "pending")
2. Contacts split into batches of 20
3. Each batch sent to Redis queue
4. Multiple workers pick up batches in parallel

### 3. Worker Processing
For each batch, worker:
1. Fetches 20 contacts from database
2. For each contact:
   - Calls email validation API
   - Calls company enrichment API
   - Updates contact with enriched data
   - Sets status to "success" or "failed"
3. Returns batch summary to parent task

### 4. Aggregation
1. Parent task waits for all batches to complete
2. Aggregator task sums up results from all batches
3. Updates Job record with final counts
4. Sets job status to "completed"

### 5. Reporting
User can check progress anytime:
- `GET /jobs/{job_id}/status` - Shows current progress, counts
- `GET /jobs/{job_id}/results` - Returns paginated enriched contacts

---

## Example Flow with Numbers

**CSV with 100 contacts:**

1. **Upload**: Job created, 100 Contact records created
2. **Distribution**: Split into 5 batches (20 contacts each)
3. **Processing**: 5 workers process batches simultaneously
   - Worker 1: Batch 1 (contacts 1-20)
   - Worker 2: Batch 2 (contacts 21-40)
   - Worker 3: Batch 3 (contacts 41-60)
   - Worker 4: Batch 4 (contacts 61-80)
   - Worker 5: Batch 5 (contacts 81-100)
4. **Results**: Each worker returns summary (e.g., "18 success, 2 failed")
5. **Aggregation**: Parent combines all results
6. **Final**: Job shows "95 success, 5 failed, 100 total"

---

## Key Celery Patterns

### group()
Runs tasks in parallel:
```python
group([process_batch.s(batch1), process_batch.s(batch2)])
```

### chord()
Runs tasks in parallel, then aggregates:
```python
chord(
    group([task1.s(), task2.s(), task3.s()])
)(aggregate_results.s())
```

---

## Configuration

**Batch Size**: 2 contacts per batch  
**Workers**: 4 concurrent workers  
**Retries**: Up to 3 attempts per failed task  
**Timeout**: 5 minutes per batch

---

## Monitoring

- **Flower Dashboard**: http://localhost:5555 - View active tasks, worker status
- **Status Endpoint**: Real-time progress updates
- **Django Admin**: View Contact and Job records
