Binance Futures Testnet Trading Bot

A Python-based trading bot built for the Binance Futures Testnet (USDT-M). This project features a modern Terminal User Interface (TUI) with real-time charting, wallet tracking, and an interactive command-line interface for placing trades.

Features

Direct REST API Integration: Places MARKET and LIMIT orders using HMAC-SHA256 signature authentication without relying on heavy third-party wrapper libraries.

Interactive TUI: Built with Textual, featuring asynchronous background updates to prevent UI freezing during network calls.

Real-Time Data: Displays live wallet balances, recent trade history, and a dynamic 24-hour trend sparkline.

Robust Logging: Comprehensive file-based logging (bot.log) configured to be UI-safe.

Prerequisites

Python 3.8+

A Binance Futures Testnet account (You can create one at demo.binance.com).

Setup Instructions

1. Install Dependencies
First, install the required Python packages using the provided requirements file:

pip install -r requirements.txt


2. Configure Environment Variables (Crucial Step)
This application requires your Binance Testnet API credentials to function. You must create a .env file to store these securely.

Create a new file named .env in the root directory of this project (in the same folder as tui.py).

Open the .env file and add your credentials exactly like this:

BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_secret_key_here


⚠️ Security Warning: Never commit your .env file to version control. If you are pushing this to a public repository, ensure .env is listed in your .gitignore file.

How to Run

Launch the interactive dashboard by running the following command in your terminal:

python tui.py


Supported Commands

Once the TUI is running, you can interact with the bot using the command input at the bottom of the screen:

buy <asset> <qty> [price] : Places a BUY order. Add a price at the end for a LIMIT order; omit it for a MARKET order.

Example Market: buy btc 0.01

Example Limit: buy btc 0.01 60000

sell <asset> <qty> [price] : Places a SELL order.

Example Limit: sell eth 0.5 3500

price <asset> : Fetches the current ticker price (e.g., price sol).

balance : Manually forces a refresh of your wallet data and graph.

help : Displays the command list inside the UI.

Note: You can use the Up and Down arrow keys to cycle through your command history!

Assumptions Made

The bot defaults to USDT-Margined contracts.

LIMIT orders currently default to GTC (Good Till Cancelled).

The TUI assumes a standard terminal size; resizing mid-session is fully supported.