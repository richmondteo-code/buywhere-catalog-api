import sys

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

sys.path.insert(0, "/home/paperclip/buywhere-api")

import app.main as main_module
from app.config import Settings
from app.main import app


def test_settings_parse_allowed_origins_csv():
    settings = Settings(ALLOWED_ORIGINS="https://app.buywhere.ai, https://admin.buywhere.ai")

    assert settings.cors_allowed_origins == [
        "https://app.buywhere.ai",
        "https://admin.buywhere.ai",
    ]


def test_settings_default_to_allow_all_in_non_production():
    settings = Settings(environment="development")

    assert settings.cors_allowed_origins == ["*"]


def test_settings_default_to_restrictive_in_production():
    settings = Settings(environment="production")

    assert settings.cors_allowed_origins == ["https://api.buywhere.ai"]


def test_app_emits_security_headers():
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert "status" in response.json()
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_app_emits_response_timing_header():
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Response-Time"].endswith("ms")
    assert float(response.headers["X-Response-Time"][:-2]) >= 0


def test_app_cors_middleware_uses_settings_allowed_origins():
    cors_middleware = next(
        middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware
    )

    assert cors_middleware.kwargs["allow_origins"] == main_module.settings.cors_allowed_origins
