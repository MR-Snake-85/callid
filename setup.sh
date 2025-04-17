#!/bin/bash

# 1. Update the package list
sudo apt update

# 2. Install essential dependencies
sudo apt install -y wget unzip curl gnupg2 software-properties-common

# 6. Install Google Chrome
sudo apt update
sudo apt install -y google-chrome-stable

pip install webdriver-manager
# 7. Install matching ChromeDriver
#CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1)
#DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
#wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip"
#unzip /tmp/chromedriver.zip -d /tmp/
#sudo mv /tmp/chromedriver /usr/local/bin/
#sudo chmod +x /usr/local/bin/chromedriver

# 8. Update package lists
sudo apt update

# 9. Install other necessary packages (including Python dependencies)
sudo apt install -y python3 python3-pip python3-venv

# 10. Install Selenium and other Python dependencies
pip3 install selenium requests

# 11. Confirm installation of necessary packages
echo "✅ Installation complete! All dependencies installed successfully."
