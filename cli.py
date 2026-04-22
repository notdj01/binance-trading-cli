import os
import logging
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, RichLog, Static, Sparkline, DataTable
from textual import work
from textual.events import Key

from bot.client import BinanceFuturesClient
from bot.orders import place_order
from bot.validators import validate_order_inputs

ASSET_MAP = {
    "bitcoin": "BTCUSDT", "btc": "BTCUSDT",
    "ethereum": "ETHUSDT", "eth": "ETHUSDT",
    "solana": "SOLUSDT", "sol": "SOLUSDT"
}


class TradingApp(App):
    # CSS: Added trend colors and table styling
    CSS = """
    Screen { layout: vertical; }
    #main-container { height: 1fr; layout: horizontal; }
    #sidebar { width: 35%; border: round cyan; padding: 1; height: 100%; layout: vertical; }
    #logs { width: 65%; border: round green; height: 100%; }
    #graph-container { margin-top: 1; border-top: solid cyan; padding-top: 1; }
    DataTable { height: 1fr; margin-top: 1; border-top: solid cyan; }
    Input { dock: bottom; margin: 1; }
    
    /* Dynamic Trend Colors */
    .trend-up { color: green; }
    .trend-down { color: red; }
    """

    def __init__(self):
        super().__init__()
        load_dotenv()
        self.client = BinanceFuturesClient()

        # Command History State
        self.history = []
        self.history_idx = -1

        # Prevent background API logs from bleeding into the UI
        bot_logger = logging.getLogger("TradingBot")
        for handler in bot_logger.handlers[:]:
            if type(handler) is logging.StreamHandler:
                bot_logger.removeHandler(handler)

    def compose(self) -> ComposeResult:
        yield Header("Binance Futures Testnet Bot")

        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield Static("Loading wallet data...", id="wallet-stats")
                yield Static("BTC 24h Trend:", id="graph-container")
                yield Sparkline(id="price-graph", summary_function=max)
                yield DataTable(id="trades-table")  # New: Recent Trades Table

            yield RichLog(id="logs", highlight=True, markup=True)

        yield Input(placeholder="Type 'help' for commands, 'exit' to leave", id="cmd-input")
        yield Footer()

    def on_mount(self):
        # Initialize the Data Table
        table = self.query_one(DataTable)
        table.add_columns("Asset", "Side", "Qty")

        self.query_one(RichLog).write(
            "[bold green]System Initialized.[/bold green] Type 'help' for commands.")
        self.update_dashboard()

    def update_sparkline_data(self, prices):
        """Thread-safe update for the sparkline, including dynamic coloring."""
        sparkline = self.query_one("#price-graph")
        sparkline.data = prices

        # Determine 24h trend (Current vs 24h ago)
        if len(prices) > 1:
            if prices[-1] >= prices[0]:
                sparkline.remove_class("trend-down")
                sparkline.add_class("trend-up")
            else:
                sparkline.remove_class("trend-up")
                sparkline.add_class("trend-down")

    def add_trade_to_table(self, symbol, side, qty):
        """Thread-safe update for the data table."""
        self.query_one(DataTable).add_row(symbol, side, qty)

    @work(thread=True)
    def update_dashboard(self):
        try:
            # Update Balances
            balances = self.client.get_account_balance()
            if balances:
                usdt_bal = next(
                    (b for b in balances if b['asset'] == 'USDT'), None)
                if usdt_bal:
                    stats = f"💰 [bold]USDT Wallet[/bold]\n"
                    stats += f"Balance: ${float(usdt_bal['balance']):.2f}\n"
                    stats += f"Available: ${float(usdt_bal['availableBalance']):.2f}\n"
                    self.call_from_thread(self.query_one(
                        "#wallet-stats").update, stats)

            # Update Graph Data
            klines = self.client.get_klines("BTCUSDT", "1h", 24)
            if klines:
                prices = [float(k[4]) for k in klines]
                self.call_from_thread(self.update_sparkline_data, prices)

        except Exception as e:
            self.call_from_thread(self.query_one(
                RichLog).write, f"[red]Dashboard update failed: {e}[/red]")

    @work(thread=True)
    def process_command(self, cmd_str: str):
        log = self.query_one(RichLog)
        parts = cmd_str.lower().strip().split()
        if not parts:
            return

        action = parts[0]

        if action == 'exit':
            return
        if action == "help":
            log.write("Supported Commands:")
            log.write(
                " - [cyan]buy [asset] [qty] [price*][/cyan] (e.g., buy btc 0.01)")
            log.write(
                " - [red]sell [asset] [qty] [price*][/red] (e.g., sell eth 0.5 3500)")
            log.write(
                "   [i dim]*Add a price at the end to place a LIMIT order. Omit for a MARKET order.[/i dim]")
            log.write(" - [yellow]price [asset][/yellow] (e.g., price btc)")
            log.write(" - [blue]balance[/blue] (Refreshes the dashboard)")
            return

        if action == "balance":
            self.update_dashboard()
            log.write("[green]Refreshing dashboard data...[/green]")
            return

        if action == "price":
            if len(parts) < 2:
                log.write(
                    "[red]Error: Specify an asset (e.g., 'price btc')[/red]")
                return
            symbol = ASSET_MAP.get(parts[1])
            if not symbol:
                log.write(f"[red]Error: Unknown asset '{parts[1]}'[/red]")
                return

            price_data = self.client.get_price(symbol)
            if price_data:
                log.write(
                    f"📈 [bold]{symbol}[/bold] Current Price: [yellow]${float(price_data['price']):.2f}[/yellow]")
            return

        if action in ["buy", "sell"]:
            # Check for at least 3 parts (action, asset, qty), 4th part (price) is optional
            if len(parts) < 3:
                log.write(
                    "[red]Error: Use 'buy btc 0.01' or 'buy btc 0.01 60000'[/red]")
                return

            asset = parts[1]
            qty_str = parts[2]
            # Extract price if provided
            price_str = parts[3] if len(parts) > 3 else None

            symbol = ASSET_MAP.get(asset)

            if not symbol:
                log.write(f"[red]Error: Unknown asset '{asset}'[/red]")
                return

            try:
                qty = float(qty_str)
                price = float(price_str) if price_str else None
            except ValueError:
                log.write(
                    "[red]Error: Quantity and Price must be valid numbers[/red]")
                return

            # Determine order type
            order_type = "LIMIT" if price else "MARKET"
            price_log = f" at ${price}" if price else " at MARKET"
            color = "green" if action == "buy" else "red"

            log.write(
                f"Executing [bold {color}]{action.upper()}[/] for {qty} {symbol}{price_log}...")

            try:
                # Pass the dynamically determined order_type and price to the API
                place_order(symbol, action.upper(), order_type, qty, price)
                log.write(
                    "[bold green]Order API call completed! Check bot.log for details.[/bold green]")

                # Add to the recent trades table visually
                self.call_from_thread(
                    self.add_trade_to_table, symbol, action.upper(), str(qty))
                self.update_dashboard()
            except Exception as e:
                log.write(f"[bold red]System Error: {e}[/bold red]")

    def on_input_submitted(self, event: Input.Submitted):
        cmd = event.value.strip()
        event.input.value = ""

        if not cmd:
            return

        # Command History Logic
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.history_idx = len(self.history)

        self.query_one(RichLog).write(
            f"\n[bold magenta]> {cmd}[/bold magenta]")
        self.process_command(cmd)

    def on_key(self, event: Key):
        """Listens for Up/Down arrows to cycle through command history."""
        input_widget = self.query_one("#cmd-input")

        # Only trigger history if the user is focused on the input box
        if not input_widget.has_focus:
            return

        if event.key == "up":
            if self.history and self.history_idx > 0:
                self.history_idx -= 1
                input_widget.value = self.history[self.history_idx]
                input_widget.cursor_position = len(
                    input_widget.value)  # Move cursor to end

        elif event.key == "down":
            if self.history and self.history_idx < len(self.history) - 1:
                self.history_idx += 1
                input_widget.value = self.history[self.history_idx]
                input_widget.cursor_position = len(input_widget.value)
            elif self.history_idx == len(self.history) - 1:
                # If we are at the bottom of history, clear the box
                self.history_idx = len(self.history)
                input_widget.value = ""


if __name__ == "__main__":
    app = TradingApp()
    app.run()
