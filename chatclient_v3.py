from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
import time
import argparse
import requests
from datetime import datetime
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


LOGIN_URL = "https://thenorthnet.oh.3cx.us/MyPhone/c2clogin"
C2CID = 1003
MODE = 3  # 0: name+email, 1: email only, 2: name only, 3: anonymous

def save_chat_message(sender, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("chat.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {sender}: {message}\n")

def perform_login(name, email):
    params = {"login": "true", "c2cid": C2CID}
    if MODE in (0, 2): params["displayname"] = name
    if MODE in (0, 1): params["email"] = email

    headers = {"accept": "*/*", "user-agent": "Mozilla/5.0"}
    payload = {}
    if MODE in (0, 2): payload["name"] = name
    if MODE in (0, 1): payload["email"] = email

    response = requests.get(LOGIN_URL, params=params, headers=headers, json=payload)
    if response.status_code != 200:
        print("❌ Login failed")
        exit(1)

    try:
        data = response.json()
        return data["sessionId"], data["pass"], data["token"]
    except Exception as e:
        print("❌ Failed to parse login response:", e)
        exit(1)

def initialize_chat_session(name, email, token):
    session_data = {
        "binance-https://thenorthnet.oh.3cx.us": {},
        "call-us-auth-https%3A%2F%2Fthenorthnet.oh.3cx.us": {"name": name, "email": email},
        f"call-us-chat-active-https%3A%2F%2Fthenorthnet.oh.3cx.us{C2CID}": True,
        "call-us-token-https%3A%2F%2Fthenorthnet.oh.3cx.us": token,
        "ethereum-https://thenorthnet.oh.3cx.us": {"chainId": "0x1"},
        "loglevel": "SILENT",
        "trust:cache:timestamp": {"timestamp": int(time.time() * 1000)},
        "wplc-ga-initiated": "29"
    }

    options = Options()
    options.add_argument("--headless")  # modern headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--log-level=3")
    options.add_argument("--incognito")


# Initialize the Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get(f"https://thenorthnet.oh.3cx.us/callus/#{C2CID}")
    time.sleep(2)

    for key, value in session_data.items():
        value_js = json.dumps(value) if isinstance(value, (dict, bool)) else f'"{value}"'
        driver.execute_script(f'window.localStorage.setItem("{key}", {value_js});')

    driver.refresh()
    time.sleep(6)
    return driver

def get_agent_messages(driver):
    return driver.execute_script('''
        const host1 = document.querySelector("#container > call-us-selector");
        const root1 = host1?.shadowRoot;
        const host2 = root1?.querySelector("#wp-live-chat-by-3CX");
        const root2 = host2?.shadowRoot;
        const spans = root2?.querySelectorAll("div.msg_agent_a70fg > span");
        return spans ? Array.from(spans).map(span => span.textContent.trim()) : [];
    ''')

def send_message(driver, message):
    try:
        driver.execute_script(f'''
            const getNestedShadow = () => {{
                const host1 = document.querySelector("#container > call-us-selector");
                const root1 = host1?.shadowRoot;
                const host2 = root1?.querySelector("#wp-live-chat-by-3CX");
                const root2 = host2?.shadowRoot;
                const textarea = root2?.querySelector("textarea");
                const sendBtn = root2?.querySelector("#sendBtn");
                if (textarea && sendBtn) {{
                    textarea.value = "{message}";
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    sendBtn.click();
                }}
            }};
            getNestedShadow();
        ''')
        save_chat_message("Me", message)
        print(f"🧑 Sent message: {message}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

def wait_for_real_agent_reply(driver, previous_messages, timeout=600):
    seen = set(previous_messages)
    print("⏳ Waiting for agent reply...\n")
    start_time = time.time()
    replied = False

    while time.time() - start_time < timeout:
        try:
            messages = get_agent_messages(driver)
            for msg in messages:
                if msg not in seen:
                    print(f"💬 Agent: {msg}")
                    save_chat_message("Agent", msg)
                    replied = True
                    return
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error reading agent message: {e}")

    if not replied:
        print("⌛ No reply received from agent in 10 minutes.")
        save_chat_message("System", "No agent reply in 10 minutes.")

if __name__ == "__main__":
    open("chat.txt", "w").close()

    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Your name")
    parser.add_argument("--email", help="Your email")
    parser.add_argument("--message", required=True, help="Message to send")
    args = parser.parse_args()

    name = args.name or ""
    email = args.email or ""

    if MODE == 0 and (not name or not email):
        parser.error("Mode 0 requires both --name and --email")
    elif MODE == 1 and not email:
        parser.error("Mode 1 requires --email")
    elif MODE == 2 and not name:
        parser.error("Mode 2 requires --name")

    print("🔐 Logging in...")
    session_id, pwd, token = perform_login(name, email)

    print("✅ Login success. Initializing chat session...")
    driver = initialize_chat_session(name, email, token)

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

    driver.quit()
    print("🚪 Chat session ended.")
