import re

with open('coredent-api/app/api/v1/endpoints/billing.py', 'r') as f:
    content = f.read()

# Remove all "Convert string UUID to UUID object" blocks and replace variable usage
patterns = [
    # pattern for standalone try/except blocks
    (r'    # Convert string UUID to UUID object\n    try:\n        (\w+)_uuid = UUID\((\w+)\)\n    except ValueError:\n        raise HTTPException\(status_code=status\.HTTP_400_BAD_REQUEST, detail="Invalid [^"]+ ID format"\)\n    \n    ', '    '),
    # pattern for inline query blocks (list_invoices patient_id)
    (r'        # Convert string UUID to UUID object\n        try:\n            (\w+)_uuid = UUID\((\w+)\)\n            query = query\.where\(([^)]+) == (\w+)_uuid\)\n        except ValueError:\n            raise HTTPException\(status_code=status\.HTTP_400_BAD_REQUEST, detail="Invalid [^"]+ ID format"\)\n', r'        query = query.where(\3 == \2)\n'),
    # pattern for inline query blocks (list_payments)
    (r'        # Convert string UUID to UUID object\n        try:\n            (\w+)_uuid = UUID\((\w+)\)\n            query = query\.where\(([^)]+) == (\w+)_uuid\)\n        except ValueError:\n            raise HTTPException\(status_code=status\.HTTP_400_BAD_REQUEST, detail="Invalid [^"]+ ID format"\)\n', r'        query = query.where(\3 == \2)\n'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Also replace any remaining _uuid references that were created from str params
# invoice_uuid -> invoice_id, payment_uuid -> payment_id, patient_uuid -> patient_id
for old, new in [('invoice_uuid', 'invoice_id'), ('payment_uuid', 'payment_id'), ('patient_uuid', 'patient_id')]:
    content = content.replace(old, new)

with open('coredent-api/app/api/v1/endpoints/billing.py', 'w') as f:
    f.write(content)

print('Done')
