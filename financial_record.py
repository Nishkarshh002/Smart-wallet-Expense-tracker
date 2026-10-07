"""
Smart Wallet & Financial Record Tracker
A complete personal finance and wallet manager with:
- Multiple payment wallets (Cash, Bank, Cards)
- Income, Expense & Inter-wallet transfers
- Visual category breakdown & percentages
- Transaction history table with search & filters
- CSV export & JSON data backup
- Integrated launcher for the companion Web App
"""

import sys
import os
import json
import csv
import webbrowser
from datetime import datetime
from typing import Dict, List, Any, Optional

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallet_data.json")
WEB_APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallet_app.html")

CATEGORIES = [
    "Food & Dining",
    "Transport & Fuel",
    "Groceries",
    "Bills & Utilities",
    "Shopping",
    "Entertainment",
    "Health & Medical",
    "Education",
    "Salary & Wages",
    "Investments",
    "Gifts & Donations",
    "General / Other"
]

DEFAULT_DATA = {
    "currency": "₹",
    "wallets": [
        {"id": "w_cash", "name": "Pocket Cash Wallet", "type": "cash", "balance": 2500.00},
        {"id": "w_bank", "name": "Main Bank (Savings)", "type": "bank", "balance": 28400.00},
        {"id": "w_card", "name": "Credit Card", "type": "card", "balance": 12000.00}
    ],
    "transactions": [
        {
            "id": "tx_1",
            "type": "income",
            "amount": 35000.00,
            "walletId": "w_bank",
            "category": "Salary & Wages",
            "note": "Monthly salary credited",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        {
            "id": "tx_2",
            "type": "transfer",
            "amount": 3000.00,
            "walletId": "w_bank",
            "destWalletId": "w_cash",
            "category": "Transfer",
            "note": "ATM cash withdrawal for wallet",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        {
            "id": "tx_3",
            "type": "expense",
            "amount": 450.00,
            "walletId": "w_cash",
            "category": "Food & Dining",
            "note": "Lunch with friends",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    ]
}


class WalletManager:
    """Core logic engine for managing wallets and transactions."""

    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.data_file):
            self._save_data(DEFAULT_DATA)
            return json.loads(json.dumps(DEFAULT_DATA))
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("currency", "₹")
                data.setdefault("wallets", [])
                data.setdefault("transactions", [])
                return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_DATA))

    def _save_data(self, data: Dict[str, Any]):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save(self):
        self._save_data(self.data)

    @property
    def currency(self) -> str:
        return self.data.get("currency", "₹")

    @currency.setter
    def currency(self, val: str):
        self.data["currency"] = val
        self.save()

    def get_wallets(self) -> List[Dict[str, Any]]:
        return self.data["wallets"]

    def get_wallet(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        for w in self.data["wallets"]:
            if w["id"] == wallet_id:
                return w
        return None

    def add_wallet(self, name: str, wallet_type: str, initial_balance: float = 0.0) -> Dict[str, Any]:
        wallet_id = "w_" + datetime.now().strftime("%y%m%d%H%M%S")
        wallet = {
            "id": wallet_id,
            "name": name,
            "type": wallet_type,
            "balance": float(initial_balance)
        }
        self.data["wallets"].append(wallet)
        self.save()
        return wallet

    def update_wallet_balance(self, wallet_id: str, new_balance: float):
        wallet = self.get_wallet(wallet_id)
        if wallet:
            wallet["balance"] = float(new_balance)
            self.save()

    def delete_wallet(self, wallet_id: str) -> bool:
        if len(self.data["wallets"]) <= 1:
            return False
        self.data["wallets"] = [w for w in self.data["wallets"] if w["id"] != wallet_id]
        self.save()
        return True

    def get_total_balance(self) -> float:
        return sum(float(w.get("balance", 0.0)) for w in self.data["wallets"])

    def add_transaction(
        self,
        tx_type: str,
        amount: float,
        wallet_id: str,
        category: str,
        note: str = "",
        dest_wallet_id: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        amount = float(amount)
        if amount <= 0:
            return None

        src_wallet = self.get_wallet(wallet_id)
        if not src_wallet:
            return None

        if tx_type == "expense":
            src_wallet["balance"] -= amount
        elif tx_type == "income":
            src_wallet["balance"] += amount
        elif tx_type == "transfer":
            if not dest_wallet_id or dest_wallet_id == wallet_id:
                return None
            dest_wallet = self.get_wallet(dest_wallet_id)
            if not dest_wallet:
                return None
            src_wallet["balance"] -= amount
            dest_wallet["balance"] += amount
            category = "Transfer"

        tx_id = "tx_" + datetime.now().strftime("%y%m%d%H%M%S%f")[:16]
        tx = {
            "id": tx_id,
            "type": tx_type,
            "amount": amount,
            "walletId": wallet_id,
            "destWalletId": dest_wallet_id,
            "category": category,
            "note": note,
            "date": date_str or datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.data["transactions"].insert(0, tx)
        self.save()
        return tx

    def delete_transaction(self, tx_id: str) -> bool:
        tx = None
        for item in self.data["transactions"]:
            if item["id"] == tx_id:
                tx = item
                break
        if not tx:
            return False

        # Revert wallet balance
        amount = float(tx["amount"])
        src_wallet = self.get_wallet(tx["walletId"])
        if src_wallet:
            if tx["type"] == "expense":
                src_wallet["balance"] += amount
            elif tx["type"] == "income":
                src_wallet["balance"] -= amount
            elif tx["type"] == "transfer":
                src_wallet["balance"] += amount
                dest_wallet = self.get_wallet(tx.get("destWalletId", ""))
                if dest_wallet:
                    dest_wallet["balance"] -= amount

        self.data["transactions"] = [t for t in self.data["transactions"] if t["id"] != tx_id]
        self.save()
        return True

    def get_category_breakdown(self, wallet_id: Optional[str] = None) -> Dict[str, float]:
        breakdown = {}
        for tx in self.data["transactions"]:
            if tx["type"] != "expense":
                continue
            if wallet_id and tx["walletId"] != wallet_id:
                continue
            cat = tx.get("category", "General / Other")
            breakdown[cat] = breakdown.get(cat, 0.0) + float(tx["amount"])
        return dict(sorted(breakdown.items(), key=lambda item: item[1], reverse=True))

    def export_csv(self, filepath: str) -> str:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Transaction ID", "Type", "Amount", "Currency", "Category",
                "Source Wallet", "Destination Wallet", "Date", "Note"
            ])
            for tx in self.data["transactions"]:
                src = self.get_wallet(tx["walletId"])
                src_name = src["name"] if src else tx["walletId"]
                dest_name = ""
                if tx.get("destWalletId"):
                    dest = self.get_wallet(tx["destWalletId"])
                    dest_name = dest["name"] if dest else tx["destWalletId"]
                writer.writerow([
                    tx["id"], tx["type"], f"{tx['amount']:.2f}", self.currency,
                    tx.get("category", ""), src_name, dest_name, tx.get("date", ""),
                    tx.get("note", "")
                ])
        return filepath


# ==============================================================================
# Modern Tkinter Desktop GUI
# ==============================================================================
def launch_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    manager = WalletManager()

    root = tk.Tk()
    root.title("Smart Wallet & Expense Tracker")
    root.geometry("1060x680")
    root.minsize(880, 580)
    root.configure(bg="#0d111a")

    # Styling colors
    C_BG = "#0d111a"
    C_CARD = "#161d2b"
    C_CARD_HOVER = "#1e2638"
    C_BORDER = "#253047"
    C_TEXT = "#f8fafc"
    C_MUTED = "#94a3b8"
    C_PRIMARY = "#6366f1"
    C_INCOME = "#10b981"
    C_EXPENSE = "#f43f5e"
    C_TRANSFER = "#0ea5e9"

    # Configure ttk styles
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=C_BG)
    style.configure("Card.TFrame", background=C_CARD, relief="flat")
    
    style.configure("Treeview",
                    background=C_CARD,
                    foreground=C_TEXT,
                    fieldbackground=C_CARD,
                    borderwidth=0,
                    font=("Segoe UI", 10),
                    rowheight=32)
    style.configure("Treeview.Heading",
                    background="#1a2334",
                    foreground=C_MUTED,
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0)
    style.map("Treeview",
              background=[("selected", "#2a3752")],
              foreground=[("selected", "#ffffff")])

    # Top Header
    header = tk.Frame(root, bg=C_BG)
    header.pack(fill="x", padx=24, pady=(18, 12))

    brand_frame = tk.Frame(header, bg=C_BG)
    brand_frame.pack(side="left")

    lbl_logo = tk.Label(brand_frame, text="💼", font=("Segoe UI Emoji", 22), bg=C_BG, fg="#ffffff")
    lbl_logo.pack(side="left", padx=(0, 10))

    title_frame = tk.Frame(brand_frame, bg=C_BG)
    title_frame.pack(side="left")
    lbl_title = tk.Label(title_frame, text="Smart Wallet & Expense Tracker", font=("Segoe UI", 15, "bold"), bg=C_BG, fg=C_TEXT)
    lbl_title.pack(anchor="w")
    lbl_sub = tk.Label(title_frame, text="Physical wallet balance & financial records", font=("Segoe UI", 9), bg=C_BG, fg=C_MUTED)
    lbl_sub.pack(anchor="w")

    # Header actions
    action_frame = tk.Frame(header, bg=C_BG)
    action_frame.pack(side="right")

    def open_web_dashboard():
        if os.path.exists(WEB_APP_FILE):
            webbrowser.open(f"file://{WEB_APP_FILE}")
        else:
            messagebox.showerror("Error", "web_app.html not found.")

    def export_csv_action():
        fpath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"wallet_export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if fpath:
            manager.export_csv(fpath)
            messagebox.showinfo("Success", f"CSV Exported successfully to:\n{fpath}")

    btn_web = tk.Button(action_frame, text="🌐 Web Dashboard", font=("Segoe UI", 9, "bold"),
                        bg="#2a334a", fg="#ffffff", activebackground="#374360",
                        relief="flat", padx=12, pady=6, cursor="hand2", command=open_web_dashboard)
    btn_web.pack(side="left", padx=4)

    btn_csv = tk.Button(action_frame, text="📄 Export CSV", font=("Segoe UI", 9, "bold"),
                        bg="#2a334a", fg="#ffffff", activebackground="#374360",
                        relief="flat", padx=12, pady=6, cursor="hand2", command=export_csv_action)
    btn_csv.pack(side="left", padx=4)

    def open_add_tx_dialog():
        AddTxDialog(root, manager, on_save=refresh_all)

    btn_add = tk.Button(action_frame, text="＋ Record Transaction", font=("Segoe UI", 10, "bold"),
                        bg=C_PRIMARY, fg="#ffffff", activebackground="#4f46e5",
                        relief="flat", padx=14, pady=6, cursor="hand2", command=open_add_tx_dialog)
    btn_add.pack(side="left", padx=(6, 0))

    # KPI Banner (Net Balance, Cash, Bank, Cards)
    kpi_frame = tk.Frame(root, bg=C_BG)
    kpi_frame.pack(fill="x", padx=24, pady=(0, 14))

    def make_kpi_card(parent, title, val_var, subtext, color=C_TEXT):
        card = tk.Frame(parent, bg=C_CARD, highlightbackground=C_BORDER, highlightthickness=1, padx=16, pady=12)
        card.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        tk.Label(card, textvariable=val_var, font=("Segoe UI", 16, "bold"), bg=C_CARD, fg=color).pack(anchor="w", pady=(2, 0))
        tk.Label(card, text=subtext, font=("Segoe UI", 8), bg=C_CARD, fg="#64748b").pack(anchor="w")
        return card

    var_total_balance = tk.StringVar()
    var_total_cash = tk.StringVar()
    var_total_bank = tk.StringVar()
    var_total_card = tk.StringVar()

    make_kpi_card(kpi_frame, "Total Net Balance", var_total_balance, "Sum across all wallets", "#818cf8")
    make_kpi_card(kpi_frame, "Cash in Wallet", var_total_cash, "Physical cash available", C_INCOME)
    make_kpi_card(kpi_frame, "Bank Balance", var_total_bank, "Savings & checking accounts", C_PRIMARY)
    make_kpi_card(kpi_frame, "Cards Balance", var_total_card, "Credit / Debit available", "#f59e0b")

    # Main Body: Left Panel (Wallets & Category Breakdown), Right Panel (Transactions Table)
    body = tk.Frame(root, bg=C_BG)
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    # LEFT COLUMN
    left_panel = tk.Frame(body, bg=C_BG, width=320)
    left_panel.pack(side="left", fill="y", padx=(0, 14))
    left_panel.pack_propagate(False)

    # Wallets section
    wallets_card = tk.Frame(left_panel, bg=C_CARD, highlightbackground=C_BORDER, highlightthickness=1, padx=14, pady=12)
    wallets_card.pack(fill="x", pady=(0, 12))

    w_head = tk.Frame(wallets_card, bg=C_CARD)
    w_head.pack(fill="x", pady=(0, 8))
    tk.Label(w_head, text="MY WALLETS", font=("Segoe UI", 9, "bold"), bg=C_CARD, fg=C_TEXT).pack(side="left")

    def open_adjust_wallet_dialog():
        AdjustWalletDialog(root, manager, on_save=refresh_all)

    btn_edit_wallet = tk.Button(w_head, text="⚙ Manage", font=("Segoe UI", 8), bg="#222b3d", fg=C_MUTED,
                                relief="flat", padx=6, pady=2, cursor="hand2", command=open_adjust_wallet_dialog)
    btn_edit_wallet.pack(side="right")

    wallet_list_frame = tk.Frame(wallets_card, bg=C_CARD)
    wallet_list_frame.pack(fill="x")

    # Category Breakdown section
    cat_card = tk.Frame(left_panel, bg=C_CARD, highlightbackground=C_BORDER, highlightthickness=1, padx=14, pady=12)
    cat_card.pack(fill="both", expand=True)

    tk.Label(cat_card, text="SPENDING BREAKDOWN", font=("Segoe UI", 9, "bold"), bg=C_CARD, fg=C_TEXT).pack(anchor="w", pady=(0, 8))
    cat_container = tk.Frame(cat_card, bg=C_CARD)
    cat_container.pack(fill="both", expand=True)

    # RIGHT COLUMN: Transactions Table
    right_panel = tk.Frame(body, bg=C_CARD, highlightbackground=C_BORDER, highlightthickness=1, padx=14, pady=12)
    right_panel.pack(side="right", fill="both", expand=True)

    # Toolbar: Filter by Wallet, Filter by Type, Search Box
    toolbar = tk.Frame(right_panel, bg=C_CARD)
    toolbar.pack(fill="x", pady=(0, 10))

    tk.Label(toolbar, text="Transactions", font=("Segoe UI", 11, "bold"), bg=C_CARD, fg=C_TEXT).pack(side="left", padx=(0, 12))

    selected_filter_wallet = tk.StringVar(value="All Wallets")
    wallet_filter_combo = ttk.Combobox(toolbar, textvariable=selected_filter_wallet, state="readonly", width=16)
    wallet_filter_combo.pack(side="left", padx=4)

    selected_filter_type = tk.StringVar(value="All Types")
    type_filter_combo = ttk.Combobox(toolbar, textvariable=selected_filter_type, state="readonly", width=12,
                                     values=["All Types", "Expense", "Income", "Transfer"])
    type_filter_combo.pack(side="left", padx=4)

    search_var = tk.StringVar()
    search_entry = tk.Entry(toolbar, textvariable=search_var, bg="#0d111a", fg=C_TEXT, insertbackground=C_TEXT,
                            relief="flat", highlightbackground=C_BORDER, highlightthickness=1, font=("Segoe UI", 9), width=18)
    search_entry.pack(side="right", padx=4)
    tk.Label(toolbar, text="🔍", bg=C_CARD, fg=C_MUTED).pack(side="right")

    # Treeview Table
    tree_frame = tk.Frame(right_panel, bg=C_CARD)
    tree_frame.pack(fill="both", expand=True)

    columns = ("id", "type", "details", "wallet", "date", "amount")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

    tree.heading("id", text="#")
    tree.heading("type", text="Type")
    tree.heading("details", text="Description / Category")
    tree.heading("wallet", text="Wallet")
    tree.heading("date", text="Date")
    tree.heading("amount", text="Amount")

    tree.column("id", width=50, stretch=False)
    tree.column("type", width=80, stretch=False)
    tree.column("details", width=220, stretch=True)
    tree.column("wallet", width=140, stretch=False)
    tree.column("date", width=120, stretch=False)
    tree.column("amount", width=110, anchor="e", stretch=False)

    tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    tree_scroll.pack(side="right", fill="y")

    # Bottom action bar for delete
    bot_bar = tk.Frame(right_panel, bg=C_CARD)
    bot_bar.pack(fill="x", pady=(10, 0))

    def delete_selected_tx():
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please select a transaction to delete.")
            return
        item_vals = tree.item(selected[0])["values"]
        tx_id = item_vals[0]
        if messagebox.askyesno("Confirm Delete", f"Delete record {tx_id}? The wallet balance will be restored."):
            manager.delete_transaction(tx_id)
            refresh_all()

    btn_del = tk.Button(bot_bar, text="🗑 Delete Selected", font=("Segoe UI", 8, "bold"),
                        bg="#3a1b24", fg=C_EXPENSE, activebackground="#4f202e",
                        relief="flat", padx=10, pady=4, cursor="hand2", command=delete_selected_tx)
    btn_del.pack(side="left")

    lbl_tx_count = tk.Label(bot_bar, text="0 records", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED)
    lbl_tx_count.pack(side="right")

    # Data Refresh Logic
    def refresh_all():
        curr = manager.currency

        # Update KPIs
        total = manager.get_total_balance()
        var_total_balance.set(f"{curr}{total:,.2f}")

        cash_bal = sum(float(w["balance"]) for w in manager.get_wallets() if w["type"] == "cash")
        bank_bal = sum(float(w["balance"]) for w in manager.get_wallets() if w["type"] == "bank")
        card_bal = sum(float(w["balance"]) for w in manager.get_wallets() if w["type"] == "card")

        var_total_cash.set(f"{curr}{cash_bal:,.2f}")
        var_total_bank.set(f"{curr}{bank_bal:,.2f}")
        var_total_card.set(f"{curr}{card_bal:,.2f}")

        # Update Wallets List on Left
        for widget in wallet_list_frame.winfo_children():
            widget.destroy()

        wallet_names = ["All Wallets"]
        for w in manager.get_wallets():
            wallet_names.append(w["name"])
            w_row = tk.Frame(wallet_list_frame, bg="#111622", padx=8, pady=6)
            w_row.pack(fill="x", pady=2)
            icon = "💵" if w["type"] == "cash" else ("🏦" if w["type"] == "bank" else "💳")
            tk.Label(w_row, text=f"{icon} {w['name']}", font=("Segoe UI", 9, "bold"), bg="#111622", fg=C_TEXT).pack(side="left")
            tk.Label(w_row, text=f"{curr}{float(w['balance']):,.2f}", font=("Segoe UI", 9, "bold"), bg="#111622", fg="#38bdf8").pack(side="right")

        wallet_filter_combo["values"] = wallet_names
        if selected_filter_wallet.get() not in wallet_names:
            selected_filter_wallet.set("All Wallets")

        # Update Category Breakdown
        for widget in cat_container.winfo_children():
            widget.destroy()

        breakdown = manager.get_category_breakdown()
        total_expense = sum(breakdown.values())

        if not breakdown or total_expense == 0:
            tk.Label(cat_container, text="No expenses recorded yet.", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED).pack(pady=20)
        else:
            for cat, amount in list(breakdown.items())[:7]:
                pct = (amount / total_expense) * 100
                row = tk.Frame(cat_container, bg=C_CARD)
                row.pack(fill="x", pady=3)
                
                info = tk.Frame(row, bg=C_CARD)
                info.pack(fill="x")
                tk.Label(info, text=cat, font=("Segoe UI", 8), bg=C_CARD, fg=C_TEXT).pack(side="left")
                tk.Label(info, text=f"{curr}{amount:,.0f} ({pct:.0f}%)", font=("Segoe UI", 8, "bold"), bg=C_CARD, fg=C_MUTED).pack(side="right")
                
                # Visual bar
                bar_bg = tk.Frame(row, bg="#242c3d", height=4)
                bar_bg.pack(fill="x", pady=(2, 0))
                bar_fill = tk.Frame(bar_bg, bg=C_PRIMARY, height=4, width=max(4, int(pct * 2.5)))
                bar_fill.pack(side="left")

        # Update Transactions Table
        for row in tree.get_children():
            tree.delete(row)

        w_filter = selected_filter_wallet.get()
        t_filter = selected_filter_type.get().lower()
        q = search_var.get().strip().lower()

        filtered = []
        for tx in manager.data["transactions"]:
            src = manager.get_wallet(tx["walletId"])
            src_name = src["name"] if src else tx["walletId"]
            dest = manager.get_wallet(tx.get("destWalletId", ""))
            dest_name = dest["name"] if dest else ""

            # Wallet filter
            if w_filter != "All Wallets" and src_name != w_filter and dest_name != w_filter:
                continue

            # Type filter
            if t_filter != "all types" and tx["type"] != t_filter:
                continue

            # Search query
            note_match = q in tx.get("note", "").lower()
            cat_match = q in tx.get("category", "").lower()
            if q and not note_match and not cat_match:
                continue

            filtered.append((tx, src_name, dest_name))

        lbl_tx_count.config(text=f"{len(filtered)} records found")

        for tx, src_name, dest_name in filtered:
            sign = "-" if tx["type"] == "expense" else ("+" if tx["type"] == "income" else "⇄")
            amt_display = f"{sign} {curr}{float(tx['amount']):,.2f}"
            
            details = tx.get("note") or tx.get("category", "")
            if tx.get("note") and tx.get("category") and tx["category"] != "Transfer":
                details = f"{tx['category']}: {tx['note']}"

            wallet_display = src_name
            if tx["type"] == "transfer" and dest_name:
                wallet_display = f"{src_name} ➔ {dest_name}"

            type_label = tx["type"].upper()
            tree.insert("", "end", values=(
                tx["id"],
                type_label,
                details,
                wallet_display,
                tx.get("date", ""),
                amt_display
            ))

    # Event bindings
    wallet_filter_combo.bind("<<ComboboxSelected>>", lambda e: refresh_all())
    type_filter_combo.bind("<<ComboboxSelected>>", lambda e: refresh_all())
    search_entry.bind("<KeyRelease>", lambda e: refresh_all())

    refresh_all()
    root.mainloop()


# ==============================================================================
# Add Transaction Dialog
# ==============================================================================
class AddTxDialog(object):
    def __init__(self, parent, manager: WalletManager, on_save=None):
        import tkinter as tk
        from tkinter import ttk, messagebox

        self.manager = manager
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("Record Transaction")
        self.win.geometry("440x480")
        self.win.resizable(False, False)
        self.win.configure(bg="#141a28")
        self.win.transient(parent)
        self.win.grab_set()

        C_CARD = "#141a28"
        C_TEXT = "#f8fafc"
        C_MUTED = "#94a3b8"

        tk.Label(self.win, text="Record New Transaction", font=("Segoe UI", 12, "bold"), bg=C_CARD, fg=C_TEXT).pack(pady=(16, 10))

        # Type buttons
        type_frame = tk.Frame(self.win, bg=C_CARD)
        type_frame.pack(fill="x", padx=24, pady=(0, 14))

        self.tx_type = tk.StringVar(value="expense")

        def set_type(t):
            self.tx_type.set(t)
            btn_exp.config(bg="#f43f5e" if t == "expense" else "#202738")
            btn_inc.config(bg="#10b981" if t == "income" else "#202738")
            btn_trf.config(bg="#0ea5e9" if t == "transfer" else "#202738")
            if t == "transfer":
                self.cat_frame.pack_forget()
                self.dest_frame.pack(fill="x", padx=24, pady=4, after=self.src_frame)
            else:
                self.dest_frame.pack_forget()
                self.cat_frame.pack(fill="x", padx=24, pady=4, before=self.src_frame)

        btn_exp = tk.Button(type_frame, text="↘ Expense", font=("Segoe UI", 9, "bold"), bg="#f43f5e", fg="white",
                            relief="flat", padx=10, pady=6, cursor="hand2", command=lambda: set_type("expense"))
        btn_exp.pack(side="left", fill="x", expand=True, padx=2)

        btn_inc = tk.Button(type_frame, text="↗ Income", font=("Segoe UI", 9, "bold"), bg="#202738", fg="white",
                            relief="flat", padx=10, pady=6, cursor="hand2", command=lambda: set_type("income"))
        btn_inc.pack(side="left", fill="x", expand=True, padx=2)

        btn_trf = tk.Button(type_frame, text="⇄ Transfer", font=("Segoe UI", 9, "bold"), bg="#202738", fg="white",
                            relief="flat", padx=10, pady=6, cursor="hand2", command=lambda: set_type("transfer"))
        btn_trf.pack(side="left", fill="x", expand=True, padx=2)

        # Amount
        f_amt = tk.Frame(self.win, bg=C_CARD)
        f_amt.pack(fill="x", padx=24, pady=4)
        tk.Label(f_amt, text="Amount:", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        self.ent_amt = tk.Entry(f_amt, font=("Segoe UI", 12, "bold"), bg="#0a0d14", fg=C_TEXT, insertbackground=C_TEXT, relief="flat", highlightthickness=1)
        self.ent_amt.pack(fill="x", pady=2)
        self.ent_amt.focus_set()

        # Category
        self.cat_frame = tk.Frame(self.win, bg=C_CARD)
        self.cat_frame.pack(fill="x", padx=24, pady=4)
        tk.Label(self.cat_frame, text="Category:", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        self.cb_cat = ttk.Combobox(self.cat_frame, values=CATEGORIES, state="readonly")
        self.cb_cat.set(CATEGORIES[0])
        self.cb_cat.pack(fill="x", pady=2)

        # Source Wallet
        self.src_frame = tk.Frame(self.win, bg=C_CARD)
        self.src_frame.pack(fill="x", padx=24, pady=4)
        tk.Label(self.src_frame, text="Wallet / Account:", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        wallet_map = {w["name"]: w["id"] for w in self.manager.get_wallets()}
        self.wallet_map = wallet_map
        self.cb_src = ttk.Combobox(self.src_frame, values=list(wallet_map.keys()), state="readonly")
        if wallet_map:
            self.cb_src.set(list(wallet_map.keys())[0])
        self.cb_src.pack(fill="x", pady=2)

        # Destination Wallet (for transfers)
        self.dest_frame = tk.Frame(self.win, bg=C_CARD)
        tk.Label(self.dest_frame, text="To Destination Wallet:", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        self.cb_dest = ttk.Combobox(self.dest_frame, values=list(wallet_map.keys()), state="readonly")
        if len(wallet_map) > 1:
            self.cb_dest.set(list(wallet_map.keys())[1])
        self.cb_dest.pack(fill="x", pady=2)

        # Note / Description
        f_note = tk.Frame(self.win, bg=C_CARD)
        f_note.pack(fill="x", padx=24, pady=4)
        tk.Label(f_note, text="Note / Description:", font=("Segoe UI", 9), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        self.ent_note = tk.Entry(f_note, font=("Segoe UI", 9), bg="#0a0d14", fg=C_TEXT, insertbackground=C_TEXT, relief="flat", highlightthickness=1)
        self.ent_note.pack(fill="x", pady=2)

        # Submit Buttons
        btn_box = tk.Frame(self.win, bg=C_CARD)
        btn_box.pack(fill="x", padx=24, pady=(20, 10))

        tk.Button(btn_box, text="Cancel", font=("Segoe UI", 9), bg="#222b3d", fg=C_MUTED, relief="flat",
                  padx=12, pady=6, cursor="hand2", command=self.win.destroy).pack(side="left")

        def submit():
            raw_amt = self.ent_amt.get().strip()
            try:
                amt = float(raw_amt)
                if amt <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid amount greater than 0.")
                return

            t = self.tx_type.get()
            src_name = self.cb_src.get()
            src_id = self.wallet_map.get(src_name)
            if not src_id:
                messagebox.showerror("Error", "Please select a wallet.")
                return

            dest_id = None
            cat = self.cb_cat.get()

            if t == "transfer":
                dest_name = self.cb_dest.get()
                dest_id = self.wallet_map.get(dest_name)
                if not dest_id or dest_id == src_id:
                    messagebox.showerror("Error", "Source and destination wallets must be different.")
                    return
                cat = "Transfer"

            note = self.ent_note.get().strip()
            self.manager.add_transaction(
                tx_type=t,
                amount=amt,
                wallet_id=src_id,
                category=cat,
                note=note,
                dest_wallet_id=dest_id
            )
            if self.on_save:
                self.on_save()
            self.win.destroy()

        tk.Button(btn_box, text="Save Record", font=("Segoe UI", 9, "bold"), bg="#6366f1", fg="white", relief="flat",
                  padx=16, pady=6, cursor="hand2", command=submit).pack(side="right")


# ==============================================================================
# Adjust Wallet Balance & Add Wallet Dialog
# ==============================================================================
class AdjustWalletDialog(object):
    def __init__(self, parent, manager: WalletManager, on_save=None):
        import tkinter as tk
        from tkinter import ttk, messagebox

        self.manager = manager
        self.on_save = on_save

        self.win = tk.Toplevel(parent)
        self.win.title("Manage Wallets & Balances")
        self.win.geometry("420x460")
        self.win.resizable(False, False)
        self.win.configure(bg="#141a28")
        self.win.transient(parent)
        self.win.grab_set()

        C_CARD = "#141a28"
        C_TEXT = "#f8fafc"
        C_MUTED = "#94a3b8"

        tk.Label(self.win, text="Manage Wallets & Set Balances", font=("Segoe UI", 11, "bold"), bg=C_CARD, fg=C_TEXT).pack(pady=(16, 12))

        # Adjust existing wallet
        f_exist = tk.LabelFrame(self.win, text="Update Existing Balance", bg=C_CARD, fg=C_MUTED, font=("Segoe UI", 8), padx=10, pady=8)
        f_exist.pack(fill="x", padx=20, pady=6)

        tk.Label(f_exist, text="Select Wallet:", font=("Segoe UI", 8), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        wallet_map = {w["name"]: w["id"] for w in self.manager.get_wallets()}
        cb_wallets = ttk.Combobox(f_exist, values=list(wallet_map.keys()), state="readonly")
        if wallet_map:
            cb_wallets.set(list(wallet_map.keys())[0])
        cb_wallets.pack(fill="x", pady=2)

        tk.Label(f_exist, text="Set New Balance:", font=("Segoe UI", 8), bg=C_CARD, fg=C_MUTED).pack(anchor="w", pady=(6, 0))
        ent_bal = tk.Entry(f_exist, font=("Segoe UI", 10), bg="#0a0d14", fg=C_TEXT, relief="flat", highlightthickness=1)
        ent_bal.pack(fill="x", pady=2)

        def sync_selected_bal(*args):
            w_id = wallet_map.get(cb_wallets.get())
            if w_id:
                w = self.manager.get_wallet(w_id)
                if w:
                    ent_bal.delete(0, "end")
                    ent_bal.insert(0, f"{float(w['balance']):.2f}")

        cb_wallets.bind("<<ComboboxSelected>>", sync_selected_bal)
        sync_selected_bal()

        def update_bal():
            w_id = wallet_map.get(cb_wallets.get())
            try:
                new_b = float(ent_bal.get().strip())
                self.manager.update_wallet_balance(w_id, new_b)
                if self.on_save:
                    self.on_save()
                messagebox.showinfo("Updated", f"Balance for {cb_wallets.get()} updated to {self.manager.currency}{new_b:,.2f}")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number.")

        tk.Button(f_exist, text="Update Balance", font=("Segoe UI", 8, "bold"), bg="#243048", fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", command=update_bal).pack(anchor="e", pady=(6, 0))

        # Add new wallet
        f_new = tk.LabelFrame(self.win, text="Create New Wallet", bg=C_CARD, fg=C_MUTED, font=("Segoe UI", 8), padx=10, pady=8)
        f_new.pack(fill="x", padx=20, pady=10)

        tk.Label(f_new, text="Wallet Name:", font=("Segoe UI", 8), bg=C_CARD, fg=C_MUTED).pack(anchor="w")
        ent_new_name = tk.Entry(f_new, font=("Segoe UI", 9), bg="#0a0d14", fg=C_TEXT, relief="flat", highlightthickness=1)
        ent_new_name.pack(fill="x", pady=2)

        tk.Label(f_new, text="Wallet Type:", font=("Segoe UI", 8), bg=C_CARD, fg=C_MUTED).pack(anchor="w", pady=(4, 0))
        cb_type = ttk.Combobox(f_new, values=["cash", "bank", "card", "savings"], state="readonly")
        cb_type.set("cash")
        cb_type.pack(fill="x", pady=2)

        tk.Label(f_new, text="Initial Balance:", font=("Segoe UI", 8), bg=C_CARD, fg=C_MUTED).pack(anchor="w", pady=(4, 0))
        ent_new_init = tk.Entry(f_new, font=("Segoe UI", 9), bg="#0a0d14", fg=C_TEXT, relief="flat", highlightthickness=1)
        ent_new_init.insert(0, "0.00")
        ent_new_init.pack(fill="x", pady=2)

        def create_wallet():
            name = ent_new_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Please specify a wallet name.")
                return
            try:
                b = float(ent_new_init.get().strip())
            except ValueError:
                b = 0.0

            self.manager.add_wallet(name, cb_type.get(), b)
            if self.on_save:
                self.on_save()
            messagebox.showinfo("Created", f"Wallet '{name}' created!")
            self.win.destroy()

        tk.Button(f_new, text="＋ Add Wallet", font=("Segoe UI", 8, "bold"), bg="#6366f1", fg="white",
                  relief="flat", padx=12, pady=4, cursor="hand2", command=create_wallet).pack(anchor="e", pady=(8, 0))


# ==============================================================================
# Fallback Interactive CLI Mode
# ==============================================================================
def run_cli():
    manager = WalletManager()
    curr = manager.currency

    print("\n" + "=" * 50)
    print(f"  Smart Wallet & Expense Tracker (CLI Mode)")
    print("=" * 50)

    while True:
        total = manager.get_total_balance()
        print(f"\n[Wallet Net Balance: {curr}{total:,.2f}]")
        print("1. View Wallets & Balances")
        print("2. Record Expense")
        print("3. Record Income")
        print("4. Transfer between Wallets")
        print("5. View Category Spending Breakdown")
        print("6. View Recent Transactions")
        print("7. Export to CSV")
        print("8. Open Web Dashboard in Browser")
        print("q. Quit")

        choice = input("\nSelect an option (1-8, q): ").strip().lower()

        if choice == "q":
            print("Goodbye!")
            break

        elif choice == "1":
            print("\nYour Wallets:")
            for w in manager.get_wallets():
                icon = "💵" if w["type"] == "cash" else ("🏦" if w["type"] == "bank" else "💳")
                print(f"  {icon} {w['name']:<25} : {curr}{float(w['balance']):>10,.2f}")

        elif choice in ("2", "3"):
            tx_type = "expense" if choice == "2" else "income"
            wallets = manager.get_wallets()
            print("\nSelect Wallet:")
            for idx, w in enumerate(wallets, 1):
                print(f"  {idx}. {w['name']} (Balance: {curr}{float(w['balance']):,.2f})")
            try:
                w_idx = int(input("Wallet number: ")) - 1
                wallet = wallets[w_idx]
            except Exception:
                print("Invalid wallet.")
                continue

            try:
                amt = float(input(f"Enter {tx_type} amount: "))
                if amt <= 0:
                    print("Amount must be positive.")
                    continue
            except ValueError:
                print("Invalid amount.")
                continue

            print("\nCategories:")
            for idx, c in enumerate(CATEGORIES, 1):
                print(f"  {idx}. {c}")
            try:
                c_idx = int(input("Category number (default 1): ") or "1") - 1
                cat = CATEGORIES[c_idx]
            except Exception:
                cat = "General / Other"

            note = input("Note / Description (optional): ").strip()
            manager.add_transaction(tx_type, amt, wallet["id"], cat, note)
            print(f"Success! {tx_type.capitalize()} of {curr}{amt:,.2f} recorded.")

        elif choice == "4":
            wallets = manager.get_wallets()
            if len(wallets) < 2:
                print("You need at least 2 wallets to transfer funds.")
                continue
            print("\nSource Wallet (From):")
            for idx, w in enumerate(wallets, 1):
                print(f"  {idx}. {w['name']} (Balance: {curr}{float(w['balance']):,.2f})")
            try:
                s_idx = int(input("From wallet: ")) - 1
                src_wallet = wallets[s_idx]
            except Exception:
                print("Invalid wallet.")
                continue

            print("\nDestination Wallet (To):")
            for idx, w in enumerate(wallets, 1):
                if idx - 1 != s_idx:
                    print(f"  {idx}. {w['name']}")
            try:
                d_idx = int(input("To wallet: ")) - 1
                dest_wallet = wallets[d_idx]
                if dest_wallet["id"] == src_wallet["id"]:
                    print("Source and destination must be different.")
                    continue
            except Exception:
                print("Invalid wallet.")
                continue

            try:
                amt = float(input("Transfer amount: "))
                if amt <= 0:
                    print("Amount must be positive.")
                    continue
            except ValueError:
                print("Invalid amount.")
                continue

            note = input("Note (e.g. ATM withdrawal): ").strip()
            manager.add_transaction("transfer", amt, src_wallet["id"], "Transfer", note, dest_wallet["id"])
            print(f"Transferred {curr}{amt:,.2f} from {src_wallet['name']} to {dest_wallet['name']}.")

        elif choice == "5":
            breakdown = manager.get_category_breakdown()
            total = sum(breakdown.values())
            print(f"\nCategory Spending Breakdown (Total Spent: {curr}{total:,.2f}):")
            if not breakdown:
                print("  No expenses recorded yet.")
            for cat, amt in breakdown.items():
                pct = (amt / total * 100) if total > 0 else 0
                print(f"  - {cat:<22}: {curr}{amt:>9,.2f} ({pct:4.1f}%)")

        elif choice == "6":
            print("\nRecent Transactions:")
            for tx in manager.data["transactions"][:10]:
                src = manager.get_wallet(tx["walletId"])
                src_name = src["name"] if src else tx["walletId"]
                sign = "-" if tx["type"] == "expense" else ("+" if tx["type"] == "income" else "⇄")
                print(f"  [{tx.get('date', '')}] {tx['type'].upper():<8} {sign}{curr}{float(tx['amount']):>8,.2f} | {tx.get('category',''):<16} | {src_name} | {tx.get('note','')}")

        elif choice == "7":
            csv_path = os.path.join(os.getcwd(), f"wallet_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
            manager.export_csv(csv_path)
            print(f"Exported to CSV: {csv_path}")

        elif choice == "8":
            if os.path.exists(WEB_APP_FILE):
                webbrowser.open(f"file://{WEB_APP_FILE}")
                print("Opened Web Dashboard in default browser.")
            else:
                print("web_app.html not found.")


if __name__ == "__main__":
    # If explicitly run with --cli or in headless environment, run CLI
    if "--cli" in sys.argv:
        run_cli()
    else:
        try:
            launch_gui()
        except Exception as e:
            print(f"Could not initialize GUI ({e}). Switching to CLI mode...")
            run_cli()
