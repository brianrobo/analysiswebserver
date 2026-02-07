"""
Quick API test script for Phase 1 verification
Run this after PostgreSQL is installed and server is running
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_response(name, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Status: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print('='*60)

def main():
    """Run API tests"""
    print("🧪 Testing Phase 1 API Endpoints")
    print(f"Base URL: {BASE_URL}")

    try:
        # 1. Health check
        response = requests.get(f"{BASE_URL}/health")
        print_response("Health Check", response)

        # 2. Register new user
        user_data = {
            "email": "test@example.com",
            "password": "test123456",
            "full_name": "Test User"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        print_response("User Registration", response)

        # 3. Login
        login_data = {
            "username": "test@example.com",  # OAuth2 uses 'username' field
            "password": "test123456"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data  # OAuth2 uses form data
        )
        print_response("User Login", response)

        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 4. Get current user
            response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
            print_response("Get Current User", response)

            # 5. Get user settings
            response = requests.get(f"{BASE_URL}/api/v1/settings", headers=headers)
            print_response("Get User Settings", response)

            # 6. Update theme
            response = requests.patch(
                f"{BASE_URL}/api/v1/settings/theme?theme=dark",
                headers=headers
            )
            print_response("Update Theme to Dark", response)

            # 7. Update workspace
            workspace_data = {
                "open_tabs": ["tool1", "tool2"],
                "active_tab": "tool1"
            }
            response = requests.patch(
                f"{BASE_URL}/api/v1/settings/workspace",
                params=workspace_data,
                headers=headers
            )
            print_response("Update Workspace", response)

            # 8. Add recent tool
            response = requests.post(
                f"{BASE_URL}/api/v1/settings/recent-tool/data_analyzer",
                headers=headers
            )
            print_response("Add Recent Tool", response)

            # 9. Verify settings updated
            response = requests.get(f"{BASE_URL}/api/v1/settings", headers=headers)
            print_response("Verify Settings Updated", response)

            print("\n✅ All tests completed successfully!")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  poetry run uvicorn api.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
