#!/usr/bin/env python3
"""
SolarMind Project Health Check
Verify that all components are properly configured and working.
"""

import sys
import os
import importlib.util
from pathlib import Path

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def check_python_syntax(filepath: str) -> bool:
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False

def check_imports(module_name: str, filepath: str) -> bool:
    """Check if a module can be imported."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False

def main():
    """Run comprehensive project health check."""
    print("🌞 SolarMind Project Health Check")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check essential files
    essential_files = [
        ("README.md", "Project documentation"),
        ("requirements.txt", "Python dependencies"),
        ("requirements-dev.txt", "Development dependencies"),
        (".env.example", "Environment template"),
        (".gitignore", "Git ignore rules"),
        ("LICENSE", "Project license"),
        ("CHANGELOG.md", "Change log"),
        ("CONTRIBUTING.md", "Contribution guidelines"),
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose setup"),
        ("Makefile", "Development automation"),
        (".pre-commit-config.yaml", "Pre-commit hooks"),
    ]
    
    print("\\n📁 Essential Files:")
    files_ok = 0
    for file_path, description in essential_files:
        if check_file_exists(file_path, description):
            files_ok += 1
    
    print(f"\\n📁 Files Status: {files_ok}/{len(essential_files)} files present")
    
    # Check Python syntax
    python_files = [
        "app.py",
        "config.py", 
        "extensions.py",
        "init_db.py",
        "models/usuario.py",
        "models/aparelho.py",
        "routes/api.py",
        "routes/auth.py",
        "routes/main.py",
        "routes/aparelhos.py",
        "services/automacao.py",
        "services/goodwe_client.py",
        "services/simula_evento.py",
        "utils/energia.py",
        "utils/errors.py",
        "utils/logger.py",
        "utils/previsao.py",
    ]
    
    print("\\n🐍 Python Syntax Check:")
    syntax_ok = 0
    for file_path in python_files:
        if os.path.exists(file_path):
            if check_python_syntax(file_path):
                print(f"✅ {file_path}")
                syntax_ok += 1
            else:
                print(f"❌ {file_path}")
        else:
            print(f"⚠️  {file_path} (file not found)")
    
    print(f"\\n🐍 Syntax Status: {syntax_ok}/{len(python_files)} files valid")
    
    # Check core imports
    print("\\n📦 Core Module Imports:")
    import_tests = [
        ("app", "app.py"),
        ("config", "config.py"),
        ("extensions", "extensions.py"),
    ]
    
    imports_ok = 0
    for module_name, file_path in import_tests:
        if check_imports(module_name, file_path):
            print(f"✅ {module_name}")
            imports_ok += 1
    
    print(f"\\n📦 Import Status: {imports_ok}/{len(import_tests)} modules importable")
    
    # Directory structure check
    print("\\n📂 Directory Structure:")
    required_dirs = [
        "models",
        "routes", 
        "services",
        "utils",
        "templates",
        "static",
        "instance"
    ]
    
    dirs_ok = 0
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f"✅ {dir_name}/")
            dirs_ok += 1
        else:
            print(f"❌ {dir_name}/")
    
    print(f"\\n📂 Directory Status: {dirs_ok}/{len(required_dirs)} directories present")
    
    # Final assessment
    print("\\n" + "=" * 50)
    total_checks = len(essential_files) + len(python_files) + len(import_tests) + len(required_dirs)
    total_passed = files_ok + syntax_ok + imports_ok + dirs_ok
    
    success_rate = (total_passed / total_checks) * 100
    
    if success_rate >= 90:
        status = "🎉 EXCELLENT"
        color = "green"
    elif success_rate >= 80:
        status = "✅ GOOD"
        color = "yellow"
    elif success_rate >= 70:
        status = "⚠️  NEEDS ATTENTION"
        color = "orange"
    else:
        status = "❌ CRITICAL ISSUES"
        color = "red"
    
    print(f"Overall Health: {status}")
    print(f"Success Rate: {success_rate:.1f}% ({total_passed}/{total_checks})")
    
    if success_rate >= 90:
        print("\\n🚀 Project is ready for deployment!")
        print("\\nNext steps:")
        print("1. Set up environment variables in .env")
        print("2. Initialize database: python init_db.py")
        print("3. Run the application: python app.py")
        print("4. For production: make deploy-check")
    else:
        print("\\n🔧 Please address the issues above before deployment.")
    
    return 0 if success_rate >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())
