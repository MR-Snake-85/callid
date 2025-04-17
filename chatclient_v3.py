#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import argparse
import requests
from datetime import datetime
import os
import signal
import sys

# Configuration
LOGIN_URL = "https://thenorthnet.oh.3cx.us/MyPhone/c2clogin"
C2CID = 1003
MODE = 3  # 0: name+email, 1: email only, 2: name only, 3: anonymous

def cleanup(signum, frame):
    """Handle cleanup on interrupt signals"""
    print("\n🛑 Received interrupt signal. Cleaning up...")
    if 'driver' in globals():
        driver.quit()
    sys.exit(0)

def save_chat_message(sender, message):
    """Save chat messages to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("chat.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {sender}: {message}\n")

def perform_login(name, email):
    """Handle the initial login request"""
    params = {"login": "true", "c2cid": C2CID}
    if MODE in (0, 2): params["displayname"] = name
    if MODE in (0, 1): params["email"] = email

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(LOGIN_URL, params=params, headers=headers)
    
    if response.status_code != 200:
        print("❌ Login failed with status:", response.status_code)
        exit(1)

    try:
        return response.json()["sessionId"], response.json()["pass"], response.json()["token"]
    except Exception as e:
        print("❌ Failed to parse login response:", e)
        exit(1)

def initialize_chat_session(name, email, token):
    """Initialize Chrome WebDriver optimized for headless VPS"""
    session_data = {
        # ... [your existing session data] ...
    }

    options = Options()
    
    # ===== ESSENTIAL FOR HEADLESS VPS =====
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # Critical for small VPS
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")  # Reduces memory usage
    
    # ===== PERFORMANCE OPTIMIZATIONS =====
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    
    # ===== STEALTH SETTINGS =====
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # ===== MEMORY MANAGEMENT =====
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-background-timer-throttling")
    
    # Set explicit Chrome binary location (critical for VPS)
    options.binary_location = "/usr/bin/google-chrome"

    try:
        service = Service(
            ChromeDriverManager().install(),
            service_args=["--verbose"],  # Helps debugging
        )
        
        driver = webdriver.Chrome(service=service, options=options)
        
        # Set session data
        driver.get(f"https://thenorthnet.oh.3cx.us/callus/#{C2CID}")
        time.sleep(2)
        
        for key, value in session_data.items():
            value_js = json.dumps(value) if isinstance(value, (dict, bool)) else f'"{value}"'
            driver.execute_script(f'window.localStorage.setItem("{key}", {value_js});')
        
        driver.refresh()
        time.sleep(6)
        return driver
        
    except Exception as e:
        print(f"❌ Chrome initialization failed: {str(e)}")
        print("⚠️  Ensure you have:")
        print("1. Installed Chrome: sudo apt install google-chrome-stable")
        print("2. Installed dependencies: sudo apt install -y libxss1 libappindicator1 libindicator7")
        exit(1)

# [Rest of your existing functions remain unchanged...]

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Initialize chat log
    open("chat.txt", "w").close()

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Your name")
    parser.add_argument("--email", help="Your email")
    parser.add_argument("--message", required=True, help="Message to send")
    args = parser.parse_args()

    # Validate arguments
    if MODE == 0 and (not args.name or not args.email):
        parser.error("Mode 0 requires both --name and --email")
    elif MODE == 1 and not args.email:
        parser.error("Mode 1 requires --email")
    elif MODE == 2 and not args.name:
        parser.error("Mode 2 requires --name")

    try:
        print("🔐 Logging in...")
        session_id, pwd, token = perform_login(args.name or "", args.email or "")

        print("✅ Login success. Initializing Chrome...")
        driver = initialize_chat_session(args.name or "", args.email or "", token)

        print("👀 Waiting for welcome message...")
        old_msgs = []
        for _ in range(20):
            old_msgs = get_agent_messages(driver)
            if old_msgs:
                print(f"📨 Welcome message received: {old_msgs[-1]}")
                save_chat_message("Agent", old_msgs[-1])
                break
            time.sleep(1)

        send_message(driver, args.message)
        wait_for_real_agent_reply(driver, old_msgs, timeout=20)

    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()
        print("🚪 Clean exit.")
