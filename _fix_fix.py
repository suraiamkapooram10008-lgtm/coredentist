import io
p = "tests/test_lab_vendor_referral_source_invoice.py"
s = io.open(p, encoding="utf-8-sig").read()
s = s.replace('ids = [l["id"] for l in listing.json()["labs"]]', 'ids = [v["id"] for v in listing.json()["labs"]]')
io.open(p, "w", encoding="utf-8-sig").write(s)
print("fixed")
