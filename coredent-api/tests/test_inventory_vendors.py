"""
Tests for Inventory Vendor Management & Reorder Rules
"""
import pytest
from httpx import AsyncClient

class TestInventoryVendors:
    """Test Inventory Vendors and Automation endpoints"""

    @pytest.mark.asyncio
    async def test_create_and_list_supplier(self, client: AsyncClient, auth_headers):
        """Test creating and listing suppliers"""
        supplier_data = {
            "name": "Acme Dental Supply",
            "contact_name": "John Doe",
            "email": "john@acmedental.com"
        }
        create_resp = await client.post("/api/v1/inventory/suppliers/", json=supplier_data, headers=auth_headers)
        assert create_resp.status_code == 200
        supplier_id = create_resp.json()["id"]

        list_resp = await client.get("/api/v1/inventory/suppliers/", headers=auth_headers)
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert "suppliers" in data
        assert any(s["id"] == supplier_id for s in data["suppliers"])

    @pytest.mark.asyncio
    async def test_create_vendor_contract(self, client: AsyncClient, auth_headers):
        """Test creating a vendor contract"""
        # First create a supplier
        supplier_resp = await client.post(
            "/api/v1/inventory/suppliers/", 
            json={"name": "Contract Supply Co"}, 
            headers=auth_headers
        )
        supplier_id = supplier_resp.json()["id"]

        contract_data = {
            "supplier_id": supplier_id,
            "contract_number": "CTR-1001",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2026-01-01T00:00:00Z",
            "discount_percentage": 10.5
        }
        resp = await client.post("/api/v1/inventory/suppliers/contracts/", json=contract_data, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["discount_percentage"] == 10.5

    @pytest.mark.asyncio
    async def test_create_reorder_rule(self, client: AsyncClient, auth_headers):
        """Test creating an automated reorder rule"""
        # Create a dummy item first
        item_resp = await client.post(
            "/api/v1/inventory/items/",
            json={"name": "Test Item", "sku": "TST-01", "current_quantity": 50},
            headers=auth_headers
        )
        item_id = item_resp.json()["id"]
        
        rule_data = {
            "item_id": item_id,
            "trigger_quantity": 20,
            "reorder_quantity": 100,
            "auto_approve": True
        }
        resp = await client.post("/api/v1/inventory/suppliers/rules/", json=rule_data, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["trigger_quantity"] == 20

    @pytest.mark.asyncio
    async def test_trigger_reorder_check(self, client: AsyncClient, auth_headers):
        """Test triggering the reorder check engine"""
        # We need an item that is below trigger threshold
        item_resp = await client.post(
            "/api/v1/inventory/items/",
            json={"name": "Low Stock Item", "sku": "LOW-01", "current_quantity": 5},
            headers=auth_headers
        )
        item_id = item_resp.json()["id"]

        supplier_resp = await client.post(
            "/api/v1/inventory/suppliers/", 
            json={"name": "Auto Supply Co"}, 
            headers=auth_headers
        )
        supplier_id = supplier_resp.json()["id"]

        rule_data = {
            "item_id": item_id,
            "supplier_id": supplier_id,
            "trigger_quantity": 10,  # 5 is below 10, should trigger
            "reorder_quantity": 50,
            "auto_approve": True     # should create a PO
        }
        await client.post("/api/v1/inventory/suppliers/rules/", json=rule_data, headers=auth_headers)

        # Trigger check
        check_resp = await client.post("/api/v1/inventory/suppliers/reorder-check", headers=auth_headers)
        assert check_resp.status_code == 200
        data = check_resp.json()
        assert "alerts_created" in data
        assert "purchase_orders_created" in data
        # Since it was below threshold, a PO should be created
        assert data["purchase_orders_created"] >= 1
