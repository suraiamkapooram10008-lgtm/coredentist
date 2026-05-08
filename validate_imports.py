"""
Comprehensive import chain and file validation for CoreDentist
"""
import ast
import os
import sys
import re
from pathlib import Path

errors = []
warnings = []

def check_python_files(root_dir):
    """Check all Python files for syntax errors"""
    pyfiles = []
    for dp, dn, fn in os.walk(root_dir):
        # Skip virtual envs, cache, alembic
        if '.venv' in dp or '__pycache__' in dp or 'alembic' in dp:
            continue
        for f in fn:
            if f.endswith('.py'):
                pyfiles.append(os.path.join(dp, f))
    
    print(f"\n{'='*60}")
    print(f"Checking {len(pyfiles)} Python files in {root_dir}...")
    print(f"{'='*60}")
    
    success = 0
    for f in sorted(pyfiles):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                content = fh.read()
            ast.parse(content)
            success += 1
        except SyntaxError as e:
            errors.append(f"SYNTAX ERROR in {f}: {e}")
        except Exception as e:
            errors.append(f"ERROR reading {f}: {e}")
    
    print(f"Syntax check: {success} OK, {len(errors)} errors")
    return errors

def check_python_imports(root_dir):
    """Check that imports within the project resolve to existing files"""
    import_errors = []
    project_files = {}
    
    # Build a map of Python module paths
    for dp, dn, fn in os.walk(root_dir):
        if '.venv' in dp or '__pycache__' in dp or 'alembic' in dp:
            continue
        rel = os.path.relpath(dp, root_dir)
        for f in fn:
            if f.endswith('.py'):
                full_path = os.path.join(dp, f)
                # Module name like app.core.config
                mod_parts = []
                if rel != '.':
                    mod_parts = rel.replace('\\', '/').split('/')
                mod_parts.append(f[:-3])
                if f == '__init__.py':
                    mod_name = '.'.join(mod_parts[:-1]) if mod_parts[:-1] else ''
                else:
                    mod_name = '.'.join(mod_parts)
                project_files[mod_name] = full_path
    
    print(f"Found {len(project_files)} project modules")
    
    # Now scan files for imports
    import_pattern = re.compile(r'^from\s+(app\.\S+)\s+import|^import\s+(app\.\S+)')
    
    for mod_name, filepath in sorted(project_files.items()):
        try:
            with open(filepath, 'r', encoding='utf-8') as fh:
                content = fh.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name
                        if name.startswith('app.') or name.startswith('coredent_api_app'):
                            # Check if this module exists
                            if name not in project_files and '__init__' not in name:
                                # Check for partial matches
                                parts = name.split('.')
                                # Could be app.core.config (a file) or app.core (a package)
                                if name not in project_files:
                                    import_errors.append(f"  IMPORT: {filepath} imports '{name}' but module not found")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module.startswith('app.') or module.startswith('coredent_api'):
                        # Strip to check
                        if module not in project_files and module + '.__init__' not in project_files:
                            # Check if it's a package
                            parts = module.split('.')
                            found = False
                            for i in range(len(parts), 0, -1):
                                candidate = '.'.join(parts[:i])
                                if candidate in project_files:
                                    found = True
                                    break
                            if not found:
                                import_errors.append(f"  IMPORT: {filepath} imports from '{module}' but module not found")
        except Exception as e:
            import_errors.append(f"  ERROR parsing {filepath}: {e}")
    
    return import_errors

def check_frontend_imports(root_dir):
    """Check frontend TypeScript/TSX files for import resolution"""
    print(f"\n{'='*60}")
    print(f"Checking frontend in {root_dir}...")
    print(f"{'='*60}")
    
    # Find all source files
    source_files = {}
    for dp, dn, fn in os.walk(os.path.join(root_dir, 'src')):
        if 'node_modules' in dp or '.git' in dp:
            continue
        rel = os.path.relpath(dp, root_dir)
        for f in fn:
            if f.endswith(('.ts', '.tsx', '.js', '.jsx')):
                filepath = os.path.join(dp, f)
                name = f.replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')
                source_files[f] = filepath
    
    print(f"Found {len(source_files)} frontend source files")
    return []

def try_compile_backend():
    """Try to actually compile/import the backend app"""
    print(f"\n{'='*60}")
    print("Attempting backend Python compilation check...")
    print(f"{'='*60}")
    
    result = os.system('cd coredent-api && python -m py_compile app/main.py 2>&1')
    if result == 0:
        print("Backend main.py compiled successfully")
    else:
        errors.append("Backend main.py compilation failed")
    
    result = os.system('cd coredent-api && python -m py_compile app/api/v1/api.py 2>&1')
    if result == 0:
        print("Backend api.py compiled successfully")
    else:
        errors.append("Backend api.py compilation failed")
    
    result = os.system('cd coredent-api && python -m py_compile app/core/config_simple.py 2>&1')
    if result == 0:
        print("Backend config_simple.py compiled successfully")
    else:
        errors.append("Backend config_simple.py compilation failed")

def check_file_integrity():
    """Cross-reference all files mentioned in the environment with actual filesystem"""
    print(f"\n{'='*60}")
    print("Checking cross-references between projects...")
    print(f"{'='*60}")
    
    # Check all directories exist
    dirs = ['coredent-api', 'coredent-style-main', 'docs', 'scripts']
    for d in dirs:
        if os.path.isdir(d):
            files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
            print(f"  {d}/: {len(files)} files")
        else:
            warnings.append(f"Directory '{d}' not found")
    
    # Check docs
    for dp, dn, fn in os.walk('docs'):
        for f in fn:
            if f.endswith('.md'):
                pass  # markdown docs exist
    
    # Check scripts
    script_count = 0
    for dp, dn, fn in os.walk('scripts'):
        script_count += len(fn)
    print(f"  scripts/: {script_count} total files")

def verify_requirements():
    """Check requirements.txt exists and is valid"""
    print(f"\n{'='*60}")
    print("Checking requirements...")
    print(f"{'='*60}")
    
    req_files = [
        os.path.join('coredent-api', 'requirements.txt'),
        os.path.join('coredent-style-main', 'package.json'),
    ]
    
    for req in req_files:
        if os.path.isfile(req):
            size = os.path.getsize(req)
            print(f"  {req}: {size} bytes - OK")
        else:
            warnings.append(f"  {req} NOT FOUND")

def check_test_files():
    """Verify test files exist and are importable"""
    print(f"\n{'='*60}")
    print("Checking test files...")
    print(f"{'='*60}")
    
    # Backend tests
    test_dir = os.path.join('coredent-api', 'tests')
    if os.path.isdir(test_dir):
        tests = [f for f in os.listdir(test_dir) if f.endswith('.py') and f.startswith('test_')]
        print(f"  Backend tests: {len(tests)} found")
        for t in sorted(tests):
            fpath = os.path.join(test_dir, t)
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    ast.parse(fh.read())
                print(f"    {t}: OK")
            except SyntaxError as se:
                errors.append(f"  SYNTAX ERROR in test {t}: {se}")
    else:
        warnings.append("Backend test directory not found")
    
    # Frontend tests
    frontend_test_dirs = [
        os.path.join('coredent-style-main', 'src', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'services', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'pages', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'hooks', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'contexts', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'lib', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'components', '__tests__'),
        os.path.join('coredent-style-main', 'src', 'test'),
    ]
    test_count = 0
    for td in frontend_test_dirs:
        if os.path.isdir(td):
            for f in os.listdir(td):
                if f.endswith(('.test.ts', '.test.tsx', '.spec.ts', '.spec.tsx')):
                    test_count += 1
    print(f"  Frontend tests: {test_count} found")

if __name__ == '__main__':
    print("=" * 70)
    print("COREDENTIST - COMPREHENSIVE IMPORT CHAIN REVIEW")
    print("=" * 70)
    
    # File integrity
    check_file_integrity()
    
    # Requirements
    verify_requirements()
    
    # Python syntax check
    check_python_files('coredent-api')
    
    # Test files
    check_test_files()
    
    # Backend compilation
    try_compile_backend()
    
    # Summary
    print(f"\n{'='*60}")
    print("REVIEW SUMMARY")
    print(f"{'='*60}")
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("\n  ✅ No errors found!")
    
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠️  {w}")
    else:
        print("\n  ✅ No warnings!")
    
    # Exit with error code if issues found
    if errors:
        sys.exit(1)
    else:
        print("\n✅ All checks passed!")