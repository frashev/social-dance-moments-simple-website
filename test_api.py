#!/usr/bin/env python
"""
Quick integration test for the Dance Song Recommender API.
Run with: python test_api.py
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_register():
    """Test user registration."""
    print("📝 Testing user registration...")
    data = {"username": "testuser1", "password": "pass123"}
    response = requests.post(f"{BASE_URL}/register", data=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_login():
    """Test user login."""
    print("\n🔐 Testing user login...")
    data = {"username": "testuser1", "password": "pass123"}
    response = requests.post(f"{BASE_URL}/login", data=data)
    print(f"   Status: {response.status_code}")
    resp_json = response.json()
    print(f"   Response: {resp_json}")
    if response.status_code == 200 and "user_id" in resp_json:
        return resp_json["user_id"]
    return None

def test_add_song(user_id):
    """Test adding a song manually."""
    print(f"\n🎵 Testing song addition (user_id={user_id})...")
    data = {"user_id": user_id, "song_name": "La Vida Es Una Sola"}
    response = requests.post(f"{BASE_URL}/recommend/song/manual", data=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_get_songs(user_id):
    """Test retrieving user's songs."""
    print(f"\n📖 Testing song retrieval (user_id={user_id})...")
    response = requests.get(f"{BASE_URL}/songs/{user_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_get_workshops():
    """Test retrieving workshops."""
    print("\n📍 Testing workshops retrieval...")
    response = requests.get(f"{BASE_URL}/workshops")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_create_workshop():
    """Test creating a workshop."""
    print("\n🎉 Testing workshop creation...")
    workshops = [
        {"city": "London", "location": "Dance Hall A", "date": "2026-02-15", "time": "19:00", "style": "salsa"},
        {"city": "Paris", "location": "Studio Bachata", "date": "2026-02-20", "time": "20:00", "style": "bachata"},
        {"city": "Berlin", "location": "Kizomba Night", "date": "2026-02-18", "time": "21:00", "style": "kizomba"},
        {"city": "Madrid", "location": "Zouk Dance Club", "date": "2026-02-22", "time": "22:00", "style": "zouk"},
    ]

    for w in workshops:
        response = requests.post(f"{BASE_URL}/workshops", data=w)
        print(f"   Created {w['style']} workshop in {w['city']}: {response.status_code}")

    return True

def test_get_workshops_with_coords():
    """Test retrieving workshops with coordinates."""
    print("\n🗺️ Testing workshops retrieval with coordinates...")
    response = requests.get(f"{BASE_URL}/workshops")
    print(f"   Status: {response.status_code}")
    data = response.json()
    workshops = data.get("workshops", [])

    # Display with coordinates
    for w in workshops[:3]:  # Show first 3
        print(f"   • {w['style'].upper()} - {w['location']} @ {w['city']}")
        if 'lat' in w:
            print(f"     Coordinates: ({w['lat']}, {w['lon']})")

    return response.status_code == 200

if __name__ == "__main__":
    print("🚀 Running Dance Song Recommender API Tests\n")
    print("=" * 50)

    try:
        # Test registration
        if not test_register():
            print("❌ Registration failed!")

        # Test login
        user_id = test_login()
        if not user_id:
            print("❌ Login failed!")
        else:
            # Test song operations
            test_add_song(user_id)
            test_get_songs(user_id)

        # Test workshops
        test_create_workshop()
        test_get_workshops_with_coords()

        print("\n" + "=" * 50)
        print("✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure the server is running: python -m uvicorn app.main:app --reload")

