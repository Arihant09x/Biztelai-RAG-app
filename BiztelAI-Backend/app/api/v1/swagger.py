"""OpenAPI Specification and Swagger UI Documentation Blueprint.

Provides interactive API exploration at /api/v1/docs.
"""

from flask import Blueprint, jsonify, render_template_string

swagger_bp = Blueprint("swagger", __name__, url_prefix="/docs")

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>BiztelAI Manufacturing SOP Copilot - API Documentation</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
  <style>
    body { margin: 0; background: #fafafa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" crossorigin></script>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js" crossorigin></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/api/v1/docs/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>
"""

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "BiztelAI Manufacturing SOP AI Copilot Backend API",
        "version": "1.0.0",
        "description": "Production-grade RAG backend assisting factory supervisors and operators with grounded SOP answers, safety guidelines, and guided procedures.",
        "contact": {
            "name": "BiztelAI Engineering",
            "email": "support@biztel.ai",
        },
    },
    "servers": [
        {"url": "/api/v1", "description": "Current Environment API v1 Base"}
    ],
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Provide access token obtained from /auth/login or /auth/register",
            }
        }
    },
    "paths": {
        "/health": {
            "get": {
                "tags": ["System Health"],
                "summary": "Liveness Probe",
                "responses": {"200": {"description": "Service is live"}}
            }
        },
        "/health/ready": {
            "get": {
                "tags": ["System Health"],
                "summary": "Readiness Probe",
                "description": "Checks database and cache/Redis connectivity.",
                "responses": {"200": {"description": "Service is ready"}}
            }
        },
        "/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register a new user",
                "responses": {"201": {"description": "User created with tokens"}}
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Authenticate with email and password",
                "responses": {"200": {"description": "JWT tokens issued"}}
            }
        },
        "/auth/refresh": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Refresh expired access token",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "New access token issued"}}
            }
        },
        "/auth/me": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get authenticated user profile",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "User profile data"}}
            }
        },
        "/documents/upload": {
            "post": {
                "tags": ["Documents"],
                "summary": "Upload manufacturing SOP PDF",
                "security": [{"BearerAuth": []}],
                "description": "Validates PDF magic bytes, SHA-256 deduplication, and enqueues Celery ingestion.",
                "responses": {"202": {"description": "Document registered and ingestion enqueued"}}
            }
        },
        "/documents": {
            "get": {
                "tags": ["Documents"],
                "summary": "List indexed SOP documents",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Paginated list of documents"}}
            }
        },
        "/documents/{id}": {
            "get": {
                "tags": ["Documents"],
                "summary": "Get document metadata and status",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Document details"}}
            },
            "delete": {
                "tags": ["Documents"],
                "summary": "Soft-delete document and chunks",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Document soft-deleted"}}
            }
        },
        "/documents/{id}/reprocess": {
            "post": {
                "tags": ["Documents"],
                "summary": "Trigger asynchronous re-indexing",
                "security": [{"BearerAuth": []}],
                "responses": {"202": {"description": "Ingestion job re-enqueued"}}
            }
        },
        "/ingestion/jobs/{job_id}": {
            "get": {
                "tags": ["Ingestion"],
                "summary": "Poll ingestion job status and progress",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Current job status and progress percentage"}}
            }
        },
        "/chat": {
            "post": {
                "tags": ["Chat & Copilot"],
                "summary": "Execute grounded RAG QA query",
                "security": [{"BearerAuth": []}],
                "description": "Performs hybrid retrieval, reranking, context engineering, and structured block output.",
                "responses": {"200": {"description": "Structured grounded response with citations"}}
            }
        },
        "/chat/stream": {
            "post": {
                "tags": ["Chat & Copilot"],
                "summary": "Stream grounded answer via Server-Sent Events (SSE)",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "SSE text/event-stream"}}
            }
        },
        "/procedures/generate": {
            "post": {
                "tags": ["Procedures"],
                "summary": "Generate Guided Procedure checklist",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Structured procedural steps with tracking ID"}}
            }
        },
        "/procedures/{id}/progress": {
            "post": {
                "tags": ["Procedures"],
                "summary": "Update step completion progress",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Updated step status and overall progress"}}
            }
        },
        "/feedback": {
            "post": {
                "tags": ["Feedback"],
                "summary": "Submit rating and comment on generated answer",
                "security": [{"BearerAuth": []}],
                "responses": {"201": {"description": "Feedback recorded"}}
            }
        },
        "/admin/metrics": {
            "get": {
                "tags": ["Admin & Analytics"],
                "summary": "Retrieve system telemetry and query metrics",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "System health and usage stats"}}
            }
        },
        "/llm/status": {
            "get": {
                "tags": ["LLM Provider"],
                "summary": "Inspect active LLM configuration (secrets masked)",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Configured LLM provider, base URL, model"}}
            }
        },
        "/llm/test-connection": {
            "post": {
                "tags": ["LLM Provider"],
                "summary": "Test live LLM connectivity with lightweight ping",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"description": "Connectivity verified with response latency"}}
            }
        }
    }
}


@swagger_bp.route("", methods=["GET"])
def swagger_ui():
    """Serve interactive Swagger UI."""
    return render_template_string(SWAGGER_UI_HTML)


@swagger_bp.route("/openapi.json", methods=["GET"])
def openapi_json():
    """Serve OpenAPI 3.0 JSON specification."""
    return jsonify(OPENAPI_SPEC)

