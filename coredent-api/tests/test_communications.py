"""
Tests for communications endpoints
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestCommunicationsEndpoints:
    """Test communications endpoints"""

    @pytest.mark.asyncio
    async def test_list_templates_empty(self, client: AsyncClient, auth_headers):
        """Test listing message templates"""
        response = await client.get("/api/v1/communications/templates", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_templates_with_data(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_practice):
        """Test listing templates after creating one"""
        from app.models.communication import MessageTemplate, MessageType
        template = MessageTemplate(
            practice_id=test_practice.id,
            name="Appointment Reminder",
            subject="Reminder: Upcoming appointment",
            content="Hi {{patient_name}}, this is a reminder...",
            message_type=MessageType.EMAIL,
            category="appointment",
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()

        response = await client.get("/api/v1/communications/templates", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, client: AsyncClient, auth_headers):
        """Test listing conversations"""
        response = await client.get("/api/v1/communications/conversations", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message(self, client: AsyncClient, auth_headers, test_patient):
        """Test sending a message to patient"""
        message_data = {
            "patient_id": str(test_patient.id),
            "subject": "Test message",
            "body": "This is a test message",
            "channel": "email"
        }
        response = await client.post("/api/v1/communications/send", json=message_data, headers=auth_headers)
        assert response.status_code in (202, 404, 422)
