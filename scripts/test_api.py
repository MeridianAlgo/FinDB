"""
API Testing Script
Tests all endpoints of the Financial News API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, url, **kwargs):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
            print("✓ SUCCESS")
        else:
            print(f"Error: {response.text}")
            print("✗ FAILED")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"Exception: {e}")
        print("✗ FAILED")
        return False

def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("Financial News API Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Root endpoint
    results.append(test_endpoint(
        "Root Endpoint",
        "GET",
        f"{BASE_URL}/"
    ))
    
    # Test 2: Health check
    results.append(test_endpoint(
        "Health Check",
        "GET",
        f"{BASE_URL}/api/health"
    ))
    
    # Test 3: Get sources
    results.append(test_endpoint(
        "Get Sources",
        "GET",
        f"{BASE_URL}/api/sources"
    ))
    
    # Test 4: Get statistics
    results.append(test_endpoint(
        "Get Statistics",
        "GET",
        f"{BASE_URL}/api/stats"
    ))
    
    # Test 5: Get articles (limited)
    results.append(test_endpoint(
        "Get Articles (limit=3)",
        "GET",
        f"{BASE_URL}/api/articles",
        params={"limit": 3}
    ))
    
    # Test 6: Get articles by source
    results.append(test_endpoint(
        "Get Articles by Source (cnbc)",
        "GET",
        f"{BASE_URL}/api/articles",
        params={"source": "cnbc", "limit": 2}
    ))
    
    # Test 7: Get specific article
    results.append(test_endpoint(
        "Get Article by ID (id=1)",
        "GET",
        f"{BASE_URL}/api/articles/1"
    ))
    
    # Test 8: Search articles
    results.append(test_endpoint(
        "Search Articles (query=Tesla)",
        "POST",
        f"{BASE_URL}/api/search",
        json={"query": "Tesla", "limit": 3}
    ))
    
    # Test 9: Scraping status
    results.append(test_endpoint(
        "Scraping Status",
        "GET",
        f"{BASE_URL}/api/scraping/status"
    ))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("="*60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
