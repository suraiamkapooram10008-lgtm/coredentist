#!/usr/bin/env python3
"""
CoreDent PMS — Automated Security Penetration Test Script
Runs OWASP-style checks against the local or deployed API.

Usage:
    python scripts/penetration_test.py --base-url https://your-api.com
    python scripts/penetration_test.py --base-url http://localhost:3000
"""

import argparse
import sys
import json
import requests
import urllib3
from urllib.parse import urljoin
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


class PenetrationTest:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def _url(self, path: str) -> str:
        return urljoin(self.base_url + "/", path)

    def _log(self, category: str, name: str, status: str, detail: str = ""):
        color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        print(f"{color}[{status}]{Colors.RESET} {category} :: {name}")
        if detail:
            print(f"       {detail}")
        self.results.append({"category": category, "name": name, "status": status, "detail": detail})
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.warnings += 1

    # ============================================================
    # TESTS
    # ============================================================

    def test_security_headers(self):
        """Check for security headers on root response"""
        try:
            resp = self.session.get(self.base_url, timeout=10)
            headers = resp.headers
            checks = {
                "Strict-Transport-Security": "HSTS header missing",
                "X-Content-Type-Options": "nosniff missing",
                "X-Frame-Options": "Frame options missing",
                "Content-Security-Policy": "CSP header missing",
            }
            for header, msg in checks.items():
                if header in headers:
                    self._log("Headers", header, "PASS")
                else:
                    self._log("Headers", header, "WARN", msg)
        except Exception as e:
            self._log("Headers", "Connection", "FAIL", str(e))

    def test_health_endpoint_info_leak(self):
        """Ensure health endpoint doesn't leak version info"""
        try:
            resp = self.session.get(self._url("health"), timeout=10)
            data = resp.json()
            leaks = []
            for key in ["version", "app", "environment", "database_url"]:
                if key in data:
                    leaks.append(key)
            if leaks:
                self._log("InfoLeak", "Health Endpoint", "WARN", f"Exposes: {', '.join(leaks)}")
            else:
                self._log("InfoLeak", "Health Endpoint", "PASS", "Minimal info exposed")
        except Exception as e:
            self._log("InfoLeak", "Health Endpoint", "FAIL", str(e))

    def test_docs_disabled_in_prod(self):
        """Ensure Swagger/Redoc are not exposed"""
        for path in ["docs", "redoc", "openapi.json"]:
            try:
                resp = self.session.get(self._url(path), timeout=10)
                if resp.status_code == 200:
                    self._log("Docs", f"/{path}", "WARN", "API docs accessible — disable in production")
                elif resp.status_code == 404:
                    self._log("Docs", f"/{path}", "PASS", "Correctly disabled")
                else:
                    self._log("Docs", f"/{path}", "PASS", f"Status {resp.status_code}")
            except Exception as e:
                self._log("Docs", f"/{path}", "FAIL", str(e))

    def test_sql_injection_login(self):
        """Test login endpoint for basic SQL injection resistance"""
        payloads = [
            {"email": "' OR '1'='1", "password": "password"},
            {"email": "admin@example.com'--", "password": "password"},
            {"email": "1' UNION SELECT * FROM users--", "password": "password"},
        ]
        for payload in payloads:
            try:
                resp = self.session.post(
                    self._url("api/v1/auth/login"),
                    json=payload,
                    timeout=10,
                )
                if resp.status_code == 200:
                    self._log("SQLi", f"Login payload", "FAIL", f"Login succeeded with injection: {payload['email'][:30]}")
                elif resp.status_code in [401, 422, 400]:
                    self._log("SQLi", f"Login payload", "PASS", "Correctly rejected")
                else:
                    self._log("SQLi", f"Login payload", "WARN", f"Unexpected status {resp.status_code}")
            except Exception as e:
                self._log("SQLi", f"Login payload", "FAIL", str(e))

    def test_brute_force_protection(self):
        """Test account lockout after failed attempts"""
        payload = {"email": "nonexistent@example.com", "password": "wrong"}
        statuses = []
        for i in range(7):
            try:
                resp = self.session.post(self._url("api/v1/auth/login"), json=payload, timeout=10)
                statuses.append(resp.status_code)
            except Exception:
                statuses.append(0)

        if 429 in statuses:
            self._log("BruteForce", "Rate Limiting", "PASS", "429 returned after repeated failures")
        elif statuses.count(401) == len(statuses):
            self._log("BruteForce", "Rate Limiting", "WARN", "No rate limit detected — consider implementing")
        else:
            self._log("BruteForce", "Rate Limiting", "WARN", f"Unexpected pattern: {set(statuses)}")

    def test_cors_misconfiguration(self):
        """Test CORS doesn't allow wildcard origins"""
        try:
            resp = self.session.options(
                self._url("api/v1/auth/login"),
                headers={
                    "Origin": "https://evil.com",
                    "Access-Control-Request-Method": "POST",
                },
                timeout=10,
            )
            allow_origin = resp.headers.get("Access-Control-Allow-Origin", "")
            if "*" in allow_origin or "evil.com" in allow_origin:
                self._log("CORS", "Origin Validation", "FAIL", f"Reflects arbitrary origin: {allow_origin}")
            else:
                self._log("CORS", "Origin Validation", "PASS", f"Origin rejected: {allow_origin}")
        except Exception as e:
            self._log("CORS", "Origin Validation", "FAIL", str(e))

    def test_authentication_bypass(self):
        """Test protected endpoints without auth"""
        protected = [
            "api/v1/auth/me",
            "api/v1/patients",
            "api/v1/invoices",
        ]
        for path in protected:
            try:
                resp = self.session.get(self._url(path), timeout=10)
                if resp.status_code == 401:
                    self._log("Auth", f"{path}", "PASS", "Requires authentication")
                elif resp.status_code == 200:
                    self._log("Auth", f"{path}", "FAIL", "Accessible without auth!")
                else:
                    self._log("Auth", f"{path}", "WARN", f"Status {resp.status_code}")
            except Exception as e:
                self._log("Auth", f"{path}", "FAIL", str(e))

    def test_sensitive_data_exposure(self):
        """Check error responses don't leak stack traces"""
        try:
            resp = self.session.get(self._url("api/v1/patients/invalid-uuid"), timeout=10)
            body = resp.text.lower()
            leaks = []
            for term in ["traceback", "stack trace", "sqlalchemy", "postgresql", "exception"]:
                if term in body:
                    leaks.append(term)
            if leaks:
                self._log("DataExposure", "Error Messages", "FAIL", f"Leaks: {', '.join(leaks)}")
            else:
                self._log("DataExposure", "Error Messages", "PASS", "Generic error returned")
        except Exception as e:
            self._log("DataExposure", "Error Messages", "FAIL", str(e))

    def run_all(self):
        print(f"\n{Colors.BLUE}=== CoreDent Security Penetration Test ==={Colors.RESET}")
        print(f"Target: {self.base_url}")
        print(f"Time:   {datetime.now().isoformat()}\n")

        self.test_security_headers()
        self.test_health_endpoint_info_leak()
        self.test_docs_disabled_in_prod()
        self.test_sql_injection_login()
        self.test_brute_force_protection()
        self.test_cors_misconfiguration()
        self.test_authentication_bypass()
        self.test_sensitive_data_exposure()

        print(f"\n{Colors.BLUE}=== Summary ==={Colors.RESET}")
        print(f"Passed:   {Colors.GREEN}{self.passed}{Colors.RESET}")
        print(f"Warnings: {Colors.YELLOW}{self.warnings}{Colors.RESET}")
        print(f"Failed:   {Colors.RED}{self.failed}{Colors.RESET}")

        report_path = f"security_pen_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump({
                "target": self.base_url,
                "timestamp": datetime.now().isoformat(),
                "summary": {"passed": self.passed, "warnings": self.warnings, "failed": self.failed},
                "results": self.results,
            }, f, indent=2)
        print(f"\nReport saved to: {report_path}")

        return self.failed == 0


def main():
    parser = argparse.ArgumentParser(description="CoreDent Security Penetration Test")
    parser.add_argument("--base-url", default="http://localhost:3000", help="API base URL")
    args = parser.parse_args()

    tester = PenetrationTest(args.base_url)
    ok = tester.run_all()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
