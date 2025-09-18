#!/usr/bin/env python3
"""
Test script for the sales API endpoint
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:5000"

def test_sales_api():
    """Test the sales API endpoint"""
    
    print("🧪 Testing Sales API Endpoint")
    print("=" * 50)
    
    # Test 1: Total Sales (all time, non-cancelled)
    print("\n1️⃣ Testing Total Sales (All Time)")
    try:
        response = requests.get(f"{BASE_URL}/api/order-items/sales", params={
            "cancelled_by": "null",
            "include_price": "true"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total Sales: ₹{data.get('total_sales', 0):,.2f}")
            print(f"📊 Total Items: {data.get('total_items', 0)}")
            print(f"📈 Status Breakdown: {len(data.get('status_breakdown', []))} statuses")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Monthly Sales
    print("\n2️⃣ Testing Monthly Sales")
    try:
        now = datetime.now()
        start_of_month = now.replace(day=1).strftime('%Y-%m-%d')
        today = now.strftime('%Y-%m-%d')
        
        response = requests.get(f"{BASE_URL}/api/order-items/sales", params={
            "cancelled_by": "null",
            "include_price": "true",
            "start_date": start_of_month,
            "end_date": today
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Monthly Sales: ₹{data.get('total_sales', 0):,.2f}")
            print(f"📅 Period: {start_of_month} to {today}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Yearly Sales
    print("\n3️⃣ Testing Yearly Sales")
    try:
        now = datetime.now()
        start_of_year = now.replace(month=1, day=1).strftime('%Y-%m-%d')
        today = now.strftime('%Y-%m-%d')
        
        response = requests.get(f"{BASE_URL}/api/order-items/sales", params={
            "cancelled_by": "null",
            "include_price": "true",
            "start_date": start_of_year,
            "end_date": today
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Yearly Sales: ₹{data.get('total_sales', 0):,.2f}")
            print(f"📅 Period: {start_of_year} to {today}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Daily Sales
    print("\n4️⃣ Testing Daily Sales")
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        response = requests.get(f"{BASE_URL}/api/order-items/sales", params={
            "cancelled_by": "null",
            "include_price": "true",
            "start_date": today,
            "end_date": today
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Daily Sales: ₹{data.get('total_sales', 0):,.2f}")
            print(f"📅 Date: {today}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 5: Error handling
    print("\n5️⃣ Testing Error Handling")
    try:
        response = requests.get(f"{BASE_URL}/api/order-items/sales", params={
            "cancelled_by": "null",
            "include_price": "true",
            "start_date": "invalid-date"
        })
        
        if response.status_code == 400:
            print("✅ Error handling works correctly")
        else:
            print(f"⚠️ Expected 400 error, got {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Sales API Testing Complete!")

if __name__ == "__main__":
    test_sales_api()
