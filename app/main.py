from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from sqlalchemy import text
from app.router.routers import routers
from app.core.config.database import Base, engine
from app.core.config.env import get_settings

sentry_sdk.init(
    dsn=get_settings().SENTRY_DNS,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace"
)

print("initializing app")
class AppCreator():
    def __init__(self):
        self.app = FastAPI(
            title="Enemamar API",
            description="API for Enemamar Learning Platform",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            swagger_ui_parameters={"persistAuthorization": True}
        )

        allowed_origins = [
            "https://enmamar.com",
            "https://enmamarmain.netlify.app",
            "https://checkout.chapa.co/",
            "https://chapa.co",
            "https://api.chapa.co",
        ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],  # You can restrict this further
            allow_headers=["*"],  # You can restrict this too
        )

        self.app.include_router(routers)

# Drop all tables with CASCADE
# with engine.connect() as connection:
#     # Disable foreign key checks temporarily
#     connection.execute(text("DROP SCHEMA public CASCADE;"))
#     connection.execute(text("CREATE SCHEMA public;"))
#     connection.execute(text('GRANT ALL ON SCHEMA public TO postgres;'))
#     connection.execute(text('GRANT ALL ON SCHEMA public TO public;'))
#     connection.commit()

# Recreate all tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print("Error creating tables:", e)

# Create the app instance
app_creator = AppCreator()
app = app_creator.app

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

# Custom OpenAPI schema generator
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Enemamar API",
        version="1.0.0",
        description="API for Enemamar Learning Platform",
        routes=app.routes,
    )

    # Initialize components if not present
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token in the format: Bearer {token}"
        }
    }

    # Ensure schemas are initialized
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}

    # Add common error response schemas
    openapi_schema["components"]["schemas"]["HTTPValidationError"] = {
        "title": "HTTPValidationError",
        "type": "object",
        "properties": {
            "detail": {
                "title": "Detail",
                "type": "string",
                "description": "Error message"
            }
        }
    }

    openapi_schema["components"]["schemas"]["ValidationError"] = {
        "title": "ValidationError",
        "type": "object",
        "properties": {
            "loc": {
                "title": "Location",
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Error location"
            },
            "msg": {
                "title": "Message",
                "type": "string",
                "description": "Error message"
            },
            "type": {
                "title": "Error Type",
                "type": "string",
                "description": "Error type"
            }
        }
    }

    # Apply security to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"bearerAuth": []}]

            # Fix response references if needed
            if "responses" in operation:
                for status_code, response in operation["responses"].items():
                    if "content" in response and "application/json" in response["content"]:
                        content = response["content"]["application/json"]
                        if "$ref" in content.get("schema", {}):
                            # Replace $ref with the actual schema
                            ref = content["schema"]["$ref"]
                            if ref.startswith("#/components/schemas/"):
                                schema_name = ref.split("/")[-1]
                                if schema_name in openapi_schema["components"]["schemas"]:
                                    content["schema"] = openapi_schema["components"]["schemas"][schema_name]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Override the default OpenAPI schema
app.openapi = custom_openapi

# Add custom route for API documentation
@app.get("/api", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Enemamar API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )