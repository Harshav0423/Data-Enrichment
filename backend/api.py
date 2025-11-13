from ninja import NinjaAPI, Swagger

api = NinjaAPI(title="Data Enrichment API", version="1.0.0")
api.add_router("rest/", "apps.rest.api.api.router")
api.add_router("enrich/", "apps.rest.api.enrichment.router")
