import sys
sys.path.insert(0, 'coredent-api')
from app.schemas.billing import InvoiceCreate
from datetime import datetime, timedelta

data = {
    'patient_id': '12345678-1234-1234-1234-123456789012',
    'items': [
        {'description': 'Dental Cleaning', 'procedure_code': 'D1110', 'quantity': 1, 'unit_price': 150.00},
        {'description': 'X-Ray', 'procedure_code': 'D0210', 'quantity': 1, 'unit_price': 75.00},
    ],
    'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
    'notes': 'Monthly billing',
}

try:
    result = InvoiceCreate.model_validate(data)
    print('OK:', result)
except Exception as e:
    print('ERROR:', e)
