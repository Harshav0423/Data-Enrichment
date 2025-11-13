from ninja import Router, files, File
from celery_app import app as celery_app
from ..tasks import process_csv_create_batch

from ..models import Job
import csv
from io import StringIO
import os
from django.conf import settings

router = Router()


def process_file(file) -> Job:
    os.makedirs(settings.UPLOAD_ROOT, exist_ok=True)

    # Read file content and count rows
    file_content = file.read()
    decoded_content = file_content.decode("utf-8")

    # Count rows
    csv_reader = csv.reader(StringIO(decoded_content))
    rows = list(csv_reader)
    total_contacts = len(rows) - 1  # Subtract header row

    # Create job with total_count
    job = Job.objects.create(
        status="PENDING", filename=file.name, total_count=total_contacts
    )

    file_name = f"job_{job.id}_contacts.csv"
    file_path = os.path.join(settings.UPLOAD_ROOT, file_name)

    # Write file to disk
    with open(file_path, "wb+") as destination:
        destination.write(file_content)

    print(f"Job {job.id} created for file {file.name} with {total_contacts} contacts")
    return job


@router.post("/jobs/upload", response={201: dict, 400: dict}, tags=["jobs"])
def upload_job(request, file: files.UploadedFile = File(...)):
    uploaded_file = request.FILES["file"]
    if not uploaded_file.name.endswith(".csv"):
        return 400, {"error": "File must be a CSV"}

    created_job = process_file(file)
    
    # Call task with job_id and filename (JSON-serializable args)
    file_name = f"job_{created_job.id}_contacts.csv"
    task = process_csv_create_batch.delay(created_job.id, file_name)
    
    print(f"Task dispatched: {task.id}, Task state: {task.state}, Task name: {task.name}")
    print(f"Celery broker: {celery_app.conf.broker_url}")

    return 201, {
        "message": f"Created Job: {created_job.id} for file {uploaded_file.name}",
        "task_id": task.id
    }


@router.get("/jobs/{job_id}/status", response={200: dict, 400: dict}, tags=["jobs"])
def get_job_status(request, job_id: int):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return 400, {"error": "Job not found"}
    return 200, {
        "job_id": job.id,
        "status": job.status,
        "completed": ((job.success_count + job.failure_count) / job.total_count) * 100,
    }


@router.get("/jobs/{job_id}/results", response={202: None}, tags=["jobs"])
def get_job_results(request, job_id: int):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return 400, {"error": "Job not found"}
    return 202, None
