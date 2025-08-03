import requests
import sys
import json
from datetime import datetime
import time

class FinanceBotAPITester:
    def __init__(self, base_url="https://94fc53c3-b77f-43df-8a77-3378fea2713a.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_telegram_id = 123456789  # Test user ID

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        return self.run_test(
            "Get Categories",
            "GET", 
            "api/categories",
            200
        )

    def test_dashboard_endpoint_nonexistent_user(self):
        """Test dashboard for non-existent user"""
        return self.run_test(
            "Dashboard - Non-existent User",
            "GET",
            f"api/dashboard/999999999",
            200
        )

    def test_telegram_webhook_invalid_data(self):
        """Test webhook with invalid data"""
        return self.run_test(
            "Telegram Webhook - Invalid Data",
            "POST",
            "api/telegram/webhook",
            200,
            data={"invalid": "data"}
        )

    def test_telegram_webhook_valid_message(self):
        """Test webhook with valid financial message"""
        webhook_data = {
            "update_id": 123456,
            "message": {
                "message_id": 1001,
                "from": {
                    "id": self.test_telegram_id,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": self.test_telegram_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Paguei R$ 500 de aluguel"
            }
        }
        
        return self.run_test(
            "Telegram Webhook - Valid Financial Message",
            "POST",
            "api/telegram/webhook",
            200,
            data=webhook_data
        )

    def test_telegram_webhook_start_command(self):
        """Test webhook with /start command"""
        webhook_data = {
            "update_id": 123457,
            "message": {
                "message_id": 1002,
                "from": {
                    "id": self.test_telegram_id,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": self.test_telegram_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }
        
        return self.run_test(
            "Telegram Webhook - Start Command",
            "POST",
            "api/telegram/webhook",
            200,
            data=webhook_data
        )

    def test_dashboard_after_transaction(self):
        """Test dashboard after creating transaction"""
        # Wait a bit for the transaction to be processed
        time.sleep(2)
        
        return self.run_test(
            "Dashboard - After Transaction",
            "GET",
            f"api/dashboard/{self.test_telegram_id}",
            200
        )

    def test_transactions_endpoint(self):
        """Test transactions endpoint"""
        return self.run_test(
            "Get Transactions",
            "GET",
            "api/transactions",
            200
        )

    def test_multiple_financial_messages(self):
        """Test multiple different financial messages"""
        messages = [
            "Recebi R$ 2000 de salário",
            "Gastei 50 no supermercado", 
            "Paguei R$ 100 de conta de luz",
            "Recebi R$ 300 de freelance"
        ]
        
        results = []
        for i, message in enumerate(messages):
            webhook_data = {
                "update_id": 123460 + i,
                "message": {
                    "message_id": 1010 + i,
                    "from": {
                        "id": self.test_telegram_id,
                        "is_bot": False,
                        "first_name": "Test",
                        "last_name": "User",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": self.test_telegram_id,
                        "first_name": "Test",
                        "last_name": "User", 
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message
                }
            }
            
            success, response = self.run_test(
                f"Financial Message {i+1}: '{message}'",
                "POST",
                "api/telegram/webhook",
                200,
                data=webhook_data
            )
            results.append(success)
            time.sleep(1)  # Small delay between messages
            
        return all(results)

def main():
    print("🤖 Starting FinanceBot API Tests...")
    print("=" * 50)
    
    tester = FinanceBotAPITester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Categories Endpoint", tester.test_categories_endpoint),
        ("Dashboard - Non-existent User", tester.test_dashboard_endpoint_nonexistent_user),
        ("Webhook - Invalid Data", tester.test_telegram_webhook_invalid_data),
        ("Webhook - Start Command", tester.test_telegram_webhook_start_command),
        ("Webhook - Valid Financial Message", tester.test_telegram_webhook_valid_message),
        ("Dashboard - After Transaction", tester.test_dashboard_after_transaction),
        ("Transactions Endpoint", tester.test_transactions_endpoint),
        ("Multiple Financial Messages", tester.test_multiple_financial_messages),
        ("Final Dashboard Check", tester.test_dashboard_after_transaction),
    ]
    
    print(f"\n🚀 Running {len(tests)} test suites...")
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
    
    # Final results
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Tests Run: {tester.tests_run}")
    print(f"   Tests Passed: {tester.tests_passed}")
    print(f"   Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())