"""
Tests for documents endpoints
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDocumentsEndpoints:
    """Test document management endpoints"""

    @pytest.mark.asyncio
    async def test_list_templates_empty(self, client: AsyncClient, auth_headers):
        """Test listing templates when none exist"""
        response = await client.get("/api/v1/documents/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client: AsyncClient, auth_headers):
        """Test listing documents when none exist"""
        response = await client.get("/api/v1/documents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_templates_with_data(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_practice):
        """Test listing templates after creating one"""
        from app.models.document import DocumentTemplate, DocumentCategory
        template = DocumentTemplate(
            practice_id=test_practice.id,
            name="Consent Form",
            category=DocumentCategory.CONSENT,
            template_content="I consent to treatment...",
            times_used=0,
        )
        db_session.add(template)
        await db_session.commit()

        response = await client.get("/api/v1/documents/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Consent Form"

    @pytest.mark.asyncio
    async def test_create_document_success(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_practice, test_patient):
        """Test creating a document from template"""
        from app.models.document import DocumentTemplate, DocumentCategory
        template = DocumentTemplate(
            practice_id=test_practice.id,
            name="Intake Form",
            category=DocumentCategory.CONSENT,
            template_content="Patient intake...",
            times_used=0,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        response = await client.post(
            f"/api/v1/documents/?patient_id={test_patient.id}&template_id={template.id}",
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
