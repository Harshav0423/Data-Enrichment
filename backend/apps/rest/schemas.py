from ninja import Schema, files


class JobCreateSchema(Schema):
    filename: files.UploadedFile
    total_count: int


class ValidateEmailSchema(Schema):
    email: str


class CompanyInfoSchema(Schema):
    company: str
