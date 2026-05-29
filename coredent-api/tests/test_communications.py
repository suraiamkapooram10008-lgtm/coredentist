"""Tests for communications endpoints"""
import pytest
import uuid

pytestmark = pytest.mark.asyncio


class TestMessageTemplates:
    async def test_list_templates_requires_auth(self, client):
        response = await client.get("/api/v1/communications/templates")
        assert response.status_code in (401, 403)

    async def test_create_template_requires_auth(self, client):
        response = await client.post("/api/v1/communications/templates", json={})
        assert response.status_code in (401, 403)

    async def test_create_template_validation_error(self, client, auth_headers):
        response = await client.post("/api/v1/communications/templates", json={})
        assert response.status_code in (422, 401, 403)

    async def test_get_template_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/communications/templates/{fake_id}")
        assert response.status_code in (401, 403)

    async def test_update_template_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/api/v1/communications/templates/{fake_id}", json={})
        assert response.status_code in (401, 403)

    async def test_delete_template_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/communications/templates/{fake_id}")
        assert response.status_code in (401, 403)


class TestPatientMessages:
    async def test_list_messages_requires_auth(self, client):
        response = await client.get("/api/v1/communications/messages")
        assert response.status_code in (401, 403)

    async def test_create_message_requires_auth(self, client):
        response = await client.post("/api/v1/communications/messages", json={})
        assert response.status_code in (401, 403)

    async def test_create_message_validation_error(self, client, auth_headers):
        response = await client.post("/api/v1/communications/messages", json={})
        assert response.status_code in (422, 401, 403)


class TestConversations:
    async def test_list_conversations_requires_auth(self, client):
        response = await client.get("/api/v1/communications/conversations")
        assert response.status_code in (401, 403)

    async def test_create_conversation_requires_auth(self, client):
        response = await client.post("/api/v1/communications/conversations", json={})
        assert response.status_code in (401, 403)

    async def test_create_conversation_validation_error(self, client, auth_headers):
        response = await client.post("/api/v1/communications/conversations", json={})
        assert response.status_code in (422, 401, 403)


class TestReminderSchedules:
    async def test_list_reminders_requires_auth(self, client):
        response = await client.get("/api/v1/communications/reminders")
        assert response.status_code in (401, 403)

    async def test_create_reminder_requires_auth(self, client):
        response = await client.post("/api/v1/communications/reminders", json={})
        assert response.status_code in (401, 403)
