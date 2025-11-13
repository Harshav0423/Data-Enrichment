from ninja import Router, files, File
from ..models import Job, Contact
from ..schemas import ValidateEmailSchema, CompanyInfoSchema

from django.conf import settings
import random, time

router = Router()


@router.post("/validate-email", response={200: dict}, tags=["enrichment"])
def validate_email(request, payload: ValidateEmailSchema):
    # sleep
    time.sleep(random.uniform(0.5, 2.0))

    email = payload.email
    valid = False

    if email and "@" in email and "." in email.split("@")[-1]:

        valid = random.choice([True, False])
    return 200, {"valid": valid}


@router.post("/company-info", response={200: dict}, tags=["enrichment"])
def enrich_company_info(request, payload: CompanyInfoSchema):
    # sleep
    time.sleep(random.uniform(0.5, 2.0))

    company = payload.company

    domain = None
    size = None
    location = None

    if company:
        domain = f"{company.lower().replace(' ', '')}.com"
        size = random.choice(["1-10", "11-50", "51-200", "201-500", "500+"])
        location = random.choice(
            [
                "Delhi, IN",
                "New York, USA",
                "San Francisco, USA",
                "London, UK",
                "Berlin, Germany",
                "Tokyo, Japan",
            ]
        )

    return 200, {
        "company": company,
        "domain": domain,
        "size": size,
        "location": location,
    }
