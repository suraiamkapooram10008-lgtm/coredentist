#!/bin/bash
# Security Audit Script for CoreDent PMS
# Run this before each production deployment

set -e

echo "=================================="
echo "CoreDent Security Audit"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

# Function to report issue
report_issue() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
}

# Function to report warning
report_warning() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

# Function to report success
report_success() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
}

echo "1. Checking for hardcoded secrets..."
if grep -r "SECRET_KEY.*=.*['\"].*['\"]" coredent-api/app --include="*.py" | grep -v "settings\." | grep -v ".example" > /dev/null; then
    report_issue "Hardcoded secrets found in code"
else
    report_success "No hardcoded secrets found"
fi

echo ""
echo "2. Checking for localhost references..."
if grep -r "localhost\|127\.0\.0\.1" coredent-api/app coredent-style-main/src --include="*.py" --include="*.ts" --include="*.tsx" | grep -v "\.test\." | grep -v "\.spec\." | grep -v "DEV\|DEBUG" > /dev/null; then
    report_warning "Localhost references found (check if properly guarded)"
else
    report_success "No unguarded localhost references"
fi

echo ""
echo "3. Checking for console.log statements..."
if grep -r "console\.log\|console\.debug" coredent-style-main/src --include="*.ts" --include="*.tsx" | grep -v "\.test\." | grep -v "DEV\|import.meta.env.DEV" | grep -v "eslint-disable" > /dev/null; then
    report_warning "Unguarded console.log statements found"
else
    report_success "All console statements properly guarded"
fi

echo ""
echo "4. Checking environment files..."
if [ ! -f "coredent-api/.env.production" ]; then
    report_issue "Missing coredent-api/.env.production"
else
    report_success "Backend production env file exists"
fi

if [ ! -f "coredent-style-main/.env.production" ]; then
    report_issue "Missing coredent-style-main/.env.production"
else
    report_success "Frontend production env file exists"
fi

echo ""
echo "5. Checking for TODO/FIXME comments..."
TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX\|HACK" coredent-api/app coredent-style-main/src --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l || echo "0")
if [ "$TODO_COUNT" -gt 10 ]; then
    report_warning "$TODO_COUNT TODO/FIXME comments found"
else
    report_success "TODO/FIXME count acceptable ($TODO_COUNT)"
fi

echo ""
echo "6. Checking npm dependencies..."
cd coredent-style-main
if npm audit --audit-level=high 2>&1 | grep -q "found 0 vulnerabilities"; then
    report_success "No high/critical npm vulnerabilities"
else
    report_issue "High/critical npm vulnerabilities found - run 'npm audit fix'"
fi
cd ..

echo ""
echo "7. Checking Python dependencies..."
cd coredent-api
if pip list --outdated | grep -E "fastapi|sqlalchemy|pydantic|cryptography" > /dev/null; then
    report_warning "Core Python packages have updates available"
else
    report_success "Core Python packages up to date"
fi
cd ..

echo ""
echo "8. Checking for exposed API keys..."
if grep -r "AKIA\|AIza\|sk_live\|pk_live" . --include="*.py" --include="*.ts" --include="*.tsx" --include="*.env" | grep -v ".example" | grep -v ".gitignore" > /dev/null; then
    report_issue "Potential API keys found in code"
else
    report_success "No exposed API keys found"
fi

echo ""
echo "9. Checking SSL/TLS configuration..."
if [ -f "coredent-api/ssl/cert.pem" ] && [ -f "coredent-api/ssl/key.pem" ]; then
    report_success "SSL certificates found"
else
    report_warning "SSL certificates not found in coredent-api/ssl/"
fi

echo ""
echo "10. Checking backup scripts..."
if [ -f "coredent-api/scripts/backup_database.sh" ]; then
    report_success "Backup script exists"
else
    report_issue "Backup script missing"
fi

echo ""
echo "=================================="
echo "Security Audit Complete"
echo "=================================="
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo "You may proceed with deployment."
    exit 0
else
    echo -e "${RED}❌ $ISSUES_FOUND critical issue(s) found!${NC}"
    echo "Please fix these issues before deploying to production."
    exit 1
fi
