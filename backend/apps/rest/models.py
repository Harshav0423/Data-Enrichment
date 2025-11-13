from django.db.models import (
    TextChoices,
    ForeignKey,
    CASCADE,
    Model,
    CharField,
    IntegerField,
    DateTimeField,
    BooleanField,
)


class StatusChoices(TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


class Job(Model):
    filename = CharField(max_length=512)
    status = CharField(max_length=32, choices=StatusChoices.choices)
    total_count = IntegerField(default=1)
    success_count = IntegerField(default=0)
    failure_count = IntegerField(default=0)
    started_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True, blank=True)


class Batch(Model):
    job = ForeignKey(Job, related_name="batches", on_delete=CASCADE)
    batch_number = IntegerField()
    status = CharField(max_length=32, choices=StatusChoices.choices)
    total_count = IntegerField(default=1)
    processed_count = IntegerField(default=0)
    started_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True, blank=True)


class Contact(Model):
    name = CharField(max_length=256)
    email = CharField(max_length=256)
    company = CharField(max_length=256, null=True, blank=True)
    phone = CharField(max_length=32, null=True, blank=True)

    # enrichment fields
    status = CharField(
        max_length=32, choices=StatusChoices.choices, default=StatusChoices.PENDING
    )
    email_valid = BooleanField(default=False)
    company_domain = CharField(max_length=256, null=True, blank=True)
    company_size = CharField(max_length=20, null=True, blank=True)
    company_location = CharField(max_length=256, null=True, blank=True)
    processed_at = DateTimeField(null=True, blank=True)
    error_message = CharField(max_length=1024, null=True, blank=True)

    # fields
    job = ForeignKey(Job, related_name="contacts", on_delete=CASCADE)
    batch = ForeignKey(
        Batch, on_delete=CASCADE, related_name="contacts", null=True, blank=True
    )
