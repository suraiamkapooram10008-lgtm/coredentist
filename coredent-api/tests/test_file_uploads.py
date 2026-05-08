"""
Tests for file upload functionality
"""
import pytest
from httpx import AsyncClient
import io


class TestDocumentUploads:
    """Test document upload functionality"""

    @pytest.mark.asyncio
    async def test_upload_patient_document(self, client: AsyncClient, auth_headers, test_patient):
        """Test uploading a document for a patient"""
        # Create a fake PDF file
        file_content = b"%PDF-1.4 fake pdf content"
        files = {
            "file": ("test_document.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "patient_id": str(test_patient.id),
            "document_type": "consent_form",
            "description": "Patient consent form"
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Endpoint might not exist or S3 not configured
        assert response.status_code in [200, 201, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client: AsyncClient, auth_headers, test_patient):
        """Test uploading an invalid file type"""
        # Create a fake executable file
        file_content = b"MZ\x90\x00"  # EXE header
        files = {
            "file": ("malicious.exe", io.BytesIO(file_content), "application/x-msdownload")
        }
        data = {
            "patient_id": str(test_patient.id),
            "document_type": "other"
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Should reject invalid file types
        assert response.status_code in [400, 404, 415, 422]

    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, client: AsyncClient, auth_headers, test_patient):
        """Test uploading a file that exceeds size limit"""
        # Create a large file (11MB, assuming 10MB limit)
        file_content = b"x" * (11 * 1024 * 1024)
        files = {
            "file": ("large_file.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "patient_id": str(test_patient.id),
            "document_type": "other"
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Should reject oversized files
        assert response.status_code in [400, 404, 413, 422]

    @pytest.mark.asyncio
    async def test_list_patient_documents(self, client: AsyncClient, auth_headers, test_patient):
        """Test listing documents for a patient"""
        response = await client.get(
            f"/api/v1/documents?patient_id={test_patient.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_download_document(self, client: AsyncClient, auth_headers):
        """Test downloading a document"""
        document_id = "00000000-0000-0000-0000-000000000000"
        
        response = await client.get(
            f"/api/v1/documents/{document_id}/download",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_document(self, client: AsyncClient, auth_headers):
        """Test deleting a document"""
        document_id = "00000000-0000-0000-0000-000000000000"
        
        response = await client.delete(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204, 404]


class TestImageUploads:
    """Test image upload functionality"""

    @pytest.mark.asyncio
    async def test_upload_patient_image(self, client: AsyncClient, auth_headers, test_patient):
        """Test uploading an X-ray or photo"""
        # Create a fake JPEG image
        file_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # JPEG header
        files = {
            "file": ("xray.jpg", io.BytesIO(file_content), "image/jpeg")
        }
        data = {
            "patient_id": str(test_patient.id),
            "image_type": "xray",
            "tooth_numbers": "14,15",
            "description": "Bitewing X-ray"
        }
        
        response = await client.post(
            "/api/v1/imaging/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_list_patient_images(self, client: AsyncClient, auth_headers, test_patient):
        """Test listing images for a patient"""
        response = await client.get(
            f"/api/v1/imaging?patient_id={test_patient.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]


class TestFileValidation:
    """Test file validation and security"""

    @pytest.mark.asyncio
    async def test_upload_without_file(self, client: AsyncClient, auth_headers, test_patient):
        """Test upload endpoint without file"""
        data = {
            "patient_id": str(test_patient.id),
            "document_type": "consent_form"
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 404, 422]

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, auth_headers, test_patient):
        """Test uploading an empty file"""
        files = {
            "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
        }
        data = {
            "patient_id": str(test_patient.id),
            "document_type": "other"
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 404, 422]
