#!/usr/bin/env python3
"""Integration test runner with Docker backend setup"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def start_test_backend():
    """Start test backend using Docker Compose"""
    print("🚀 Starting test backend...")
    
    try:
        # Start Docker services
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.test.yml", "up", "-d"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Docker services started")
        
        # Wait for backend to be ready
        backend_url = "http://localhost:4001/api/health"
        max_retries = 30
        
        for i in range(max_retries):
            try:
                response = requests.get(backend_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Backend is ready")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"⏳ Waiting for backend... ({i+1}/{max_retries})")
            time.sleep(2)
        
        print("❌ Backend failed to start")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker services: {e}")
        return False

def stop_test_backend():
    """Stop test backend"""
    print("🛑 Stopping test backend...")
    
    try:
        subprocess.run([
            "docker-compose", "-f", "docker-compose.test.yml", "down", "-v"
        ], check=True, capture_output=True, text=True)
        print("✅ Test backend stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop backend: {e}")

def run_integration_tests():
    """Run integration tests"""
    print("🧪 Running integration tests...")
    
    # Set test environment
    os.environ["PYTEST_CURRENT_TEST"] = "integration"
    
    # Run pytest with integration marker
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/test_integration.py",
        "-m", "integration",
        "-v", "--tb=short"
    ])
    
    return result.returncode == 0

def main():
    """Main test runner"""
    print("🔧 Integration Test Runner")
    print("=" * 50)
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker or Docker Compose not found")
        print("Please install Docker to run integration tests")
        sys.exit(1)
    
    success = False
    
    try:
        # Start backend
        if not start_test_backend():
            sys.exit(1)
        
        # Run tests
        success = run_integration_tests()
        
    finally:
        # Always cleanup
        stop_test_backend()
    
    if success:
        print("✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some integration tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()