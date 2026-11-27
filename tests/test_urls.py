"""
Integration tests for the URL creation, redirect, stats, and deletion
endpoints, exercised through FastAPI's TestClient against an in-memory
SQLite database (see conftest.py).
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.url import Url


def create_url(client: TestClient, **overrides) -> dict:
    payload = {"long_url": "https://example.com/some/page"}
    payload.update(overrides)
    response = client.post("/api/v1/urls", json=payload)
    return response


class TestCreateUrl:
    def test_valid_url_is_created(self, client: TestClient) -> None:
        response = create_url(client)
        assert response.status_code == 201
        body = response.json()
        assert body["short_code"]
        assert body["short_url"].endswith(body["short_code"])
        assert body["long_url"] == "https://example.com/some/page"

    def test_invalid_url_is_rejected(self, client: TestClient) -> None:
        response = client.post("/api/v1/urls", json={"long_url": "not-a-url"})
        assert response.status_code == 422

    def test_custom_alias_is_used_as_short_code(self, client: TestClient) -> None:
        response = create_url(client, custom_alias="my-alias")
        assert response.status_code == 201
        assert response.json()["short_code"] == "my-alias"

    def test_duplicate_custom_alias_is_rejected(self, client: TestClient) -> None:
        create_url(client, custom_alias="taken")
        response = create_url(client, custom_alias="taken")
        assert response.status_code == 409

    def test_reserved_alias_is_rejected(self, client: TestClient) -> None:
        response = create_url(client, custom_alias="health")
        assert response.status_code == 400

    def test_expiration_is_set_when_requested(self, client: TestClient) -> None:
        response = create_url(client, expires_in_hours=1)
        assert response.status_code == 201
        assert response.json()["expires_at"] is not None

    def test_no_expiration_by_default(self, client: TestClient) -> None:
        response = create_url(client)
        assert response.status_code == 201
        assert response.json()["expires_at"] is None


class TestRedirect:
    def test_valid_short_code_redirects(self, client: TestClient) -> None:
        created = create_url(client).json()
        response = client.get(
            f"/{created['short_code']}", follow_redirects=False
        )
        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/some/page"

    def test_unknown_short_code_is_404(self, client: TestClient) -> None:
        response = client.get("/does-not-exist", follow_redirects=False)
        assert response.status_code == 404

    def test_expired_short_code_is_410(
        self, client: TestClient, db_session: Session
    ) -> None:
        expired = Url(
            short_code="expired1",
            long_url="https://example.com/old",
            custom_alias=True,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(expired)
        db_session.commit()

        response = client.get("/expired1", follow_redirects=False)
        assert response.status_code == 410

    def test_deactivated_short_code_is_410(self, client: TestClient) -> None:
        created = create_url(client, custom_alias="to-deactivate").json()
        client.delete(f"/api/v1/urls/{created['short_code']}")

        response = client.get(
            f"/{created['short_code']}", follow_redirects=False
        )
        assert response.status_code == 410


class TestStats:
    def test_stats_reflect_click_count_and_last_accessed(
        self, client: TestClient
    ) -> None:
        created = create_url(client, custom_alias="stats-test").json()
        short_code = created["short_code"]

        client.get(f"/{short_code}", follow_redirects=False)
        client.get(f"/{short_code}", follow_redirects=False)

        response = client.get(f"/api/v1/urls/{short_code}/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["total_clicks"] == 2
        assert body["last_accessed_at"] is not None

    def test_stats_for_unknown_code_is_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/urls/nope/stats")
        assert response.status_code == 404


class TestDelete:
    def test_delete_deactivates_url(self, client: TestClient) -> None:
        created = create_url(client, custom_alias="deletable").json()
        response = client.delete(f"/api/v1/urls/{created['short_code']}")
        assert response.status_code == 200

        stats = client.get(f"/api/v1/urls/{created['short_code']}/stats").json()
        assert stats["is_active"] is False

    def test_delete_unknown_code_is_404(self, client: TestClient) -> None:
        response = client.delete("/api/v1/urls/nope")
        assert response.status_code == 404
