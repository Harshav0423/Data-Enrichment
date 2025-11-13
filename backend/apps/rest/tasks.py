from celery import chord, shared_task
from .models import Job, Batch, Contact, StatusChoices
from .utils import parse_csv, validate_email, enrich_company_info
import datetime
from itertools import islice

def chunks(iterable, n):
    """Yield successive n-sized chunks from iterable."""
    iterator = iter(iterable)
    while batch := list(islice(iterator, n)):
        yield batch

@shared_task(bind=True, max_retries=3, retry_backoff=True, time_limit=300)
def process_csv_create_batch(self, job_id: int, file_name: str):
    """
    Read CSV, create Contact records, and organize into batches

    Args:
        self: Task instance (automatically passed by Celery due to bind=True)
        job_id: ID of the Job to process
        file_name: Name of the CSV file (e.g., 'job_1_contacts.csv')
    """
    job = Job.objects.get(id=job_id)

    contacts = parse_csv(file_name)
    batches = []

    # Create Contacts
    for i, chunk in enumerate(chunks(contacts,2)):
        batch = Batch.objects.create(
            job=job,
            batch_number=i,
            status=StatusChoices.PENDING,
            total_count=len(chunk),
        )

        # create contacts from the chunk for that batch
        contact_objs = Contact.objects.bulk_create(
            [
                Contact(
                    batch=batch, job=job, status=StatusChoices.PENDING, **contact_data
                )
                for contact_data in chunk
            ]
        )
        batches.append(batch)

    # start Job
    job.status = StatusChoices.IN_PROGRESS
    job.started_at = datetime.datetime.now()
    job.save()

    chord(process_contact_batch_data.s(batch.id) for batch in batches)(
        aggregate_batch_results.s(job_id=job.id)
    )


@shared_task
def process_contact_batch_data(batch_id: int):
    batch = Batch.objects.get(id=batch_id)
    batch.started_at = datetime.datetime.now()
    batch.status = StatusChoices.IN_PROGRESS
    batch.save()
    
    contacts = batch.contacts.filter(status=StatusChoices.PENDING)

    failed = []
    for contact in contacts:

        contact.status = StatusChoices.IN_PROGRESS
        contact.save()

        # enrichment
        try:
            # Validate email
            if contact.email:
                email_result = validate_email(contact.email)
                contact.email_valid = email_result.get("valid", False)

            # Enrich company information
            if contact.company:
                company_result = enrich_company_info(contact.company)
                contact.company_domain = company_result.get("domain")
                contact.company_size = company_result.get("size")
                contact.company_location = company_result.get("location")

            # Mark contact as completed
            contact.status = StatusChoices.SUCCESS
            contact.processed_at = datetime.datetime.now()
            contact.save()

        except Exception as e:
            failed.append(contact.id)
            contact.status = StatusChoices.FAILED
            print(f"Error processing batch: {batch.id} for contact: {contact.id} with {str(e)}")
            contact.error_message = str(e)
            contact.save()
    batch.status = StatusChoices.SUCCESS if not failed else StatusChoices.FAILED
    batch.completed_at = datetime.datetime.now()
    batch.processed_count = batch.total_count - len(failed)

    batch.save()

    return {
        "batch_id": batch.id,
        "processed": len(contacts),
        "success": len(contacts) - len(failed),
        "failed": len(failed),
        "errors": failed,
    }


@shared_task
def aggregate_batch_results(batch_results, job_id: int):
    job = Job.objects.get(id=job_id)
    total_success = 0
    total_failed = 0
    for res in batch_results:
        total_success += res.get("success", 0)
        total_failed += res.get("failed", 0)

    job.success_count = total_success
    job.failure_count = total_failed
    job.status = StatusChoices.SUCCESS if total_failed == 0 else StatusChoices.FAILED
    job.completed_at = datetime.datetime.now()
    job.save()

    return {
        "job_id": job.id,
        "total_contacts": job.total_count,
        "sucess": total_success,
        "failed": total_failed,
    }
