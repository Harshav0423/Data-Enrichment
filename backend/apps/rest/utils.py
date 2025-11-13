import os
import csv
import requests
from django.conf import settings


def parse_csv(file_name: str):
    """
    Parse CSV file and return list of contacts
    """
    file_path = os.path.join(settings.UPLOAD_ROOT, file_name)
    contacts_data = []

    with open(file_path, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            contacts_data.append(
                {
                    "name": row.get("name", ""),
                    "email": row.get("email", ""),
                    "company": row.get("company", ""),
                    "phone": row.get("phone", ""),
                }
            )

    return contacts_data


def validate_email(email: str) -> dict:
    try:
        # running locally on port 8000
        url = f"{settings.BASE_URL}/api/enrich/validate-email"
        response = requests.post(url, json={"email": email})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"email": email, "valid": False, "error": str(e)}


def enrich_company_info(company: str) -> dict:
    try:
        url = f"{settings.BASE_URL}/api/enrich/company-info"
        response = requests.post(url, json={"company": company})
        response.raise_for_status()
        print(response.json())
        return response.json()
    except Exception as e:
        return {
            "company": company,
            "domain": None,
            "size": None,
            "location": None,
            "error": str(e),
        }
