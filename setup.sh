#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "🔄 Updating package lists..."
sudo apt update

echo "📦 Installing essential system dependencies..."
sudo apt install -y wget unzip curl gnupg2 software-properties-common

echo "🌐 Downloading and installing Google Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

echo "🐍 Installing Python and virtual environment tools..."
sudo apt install -y python3 python3-pip python3-venv

echo "📚 Installing Python packages (Selenium, requests, webdriver-manager)..."
pip3 install --upgrade pip
pip3 install selenium requests webdriver-manager

echo "✅ Installation complete! All dependencies installed successfully."
