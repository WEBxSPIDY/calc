    def show_cash_flow_report(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Cash Flow Statement", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        # Simple cash flow: Receipts (credits to cash/bank), Payments (debits from cash/bank)
        tree = ttk.Treeview(self.content_frame, columns=("Type", "Account", "Amount", "Date", "Desc"), show="headings", height=14)
        for col in ("Type", "Account", "Amount", "Date", "Desc"):
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=120 if col!="Desc" else 200)
        tree.pack(pady=10, fill="x")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # Receipts: credit to cash/bank
        c.execute("SELECT credit_account, credit_amount, date, description FROM Journal WHERE credit_account LIKE '%cash%' OR credit_account LIKE '%bank%'")
        for acct, amt, date, desc in c.fetchall():
            tree.insert("", "end", values=("Receipt", acct, amt, date, desc))
        # Payments: debit from cash/bank
        c.execute("SELECT debit_account, debit_amount, date, description FROM Journal WHERE debit_account LIKE '%cash%' OR debit_account LIKE '%bank%'")
        for acct, amt, date, desc in c.fetchall():
            tree.insert("", "end", values=("Payment", acct, amt, date, desc))
        conn.close()
        # Export to Excel
        def export_cashflow():
            from tkinter import filedialog
            file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if file:
                export_to_excel(tree, file)
        tk.Button(self.content_frame, text="Export to Excel", command=export_cashflow, width=16).pack(pady=2)

    def show_ratio_analysis_report(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Ratio Analysis", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        # Example ratios: Current Ratio, Quick Ratio, Debt-Equity Ratio
        tree = ttk.Treeview(self.content_frame, columns=("Ratio", "Value"), show="headings", height=10)
        for col in ("Ratio", "Value"):
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=200)
        tree.pack(pady=10, fill="x")
        # Calculate ratios from BalanceSheet
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT category, amount FROM BalanceSheet")
        data = c.fetchall()
        conn.close()
        cats = {}
        for cat, amt in data:
            cats.setdefault(cat, 0)
            cats[cat] += amt
        # Current Ratio = Current Assets / Current Liabilities
        curr_assets = cats.get("Current Assets", 0)
        curr_liab = cats.get("Current Liabilities", 0)
        current_ratio = round(curr_assets / curr_liab, 2) if curr_liab else 'N/A'
        # Quick Ratio = (Current Assets - Inventory) / Current Liabilities (assume Inventory=0 if not present)
        inventory = cats.get("Inventory", 0)
        quick_ratio = round((curr_assets - inventory) / curr_liab, 2) if curr_liab else 'N/A'
        # Debt-Equity Ratio = Total Liabilities / Equity
        total_liab = cats.get("Current Liabilities", 0) + cats.get("Non-Current Liabilities", 0)
        equity = cats.get("Share Capital", 0) + cats.get("Reserves & Surplus", 0)
        debt_equity = round(total_liab / equity, 2) if equity else 'N/A'
        tree.insert("", "end", values=("Current Ratio", current_ratio))
        tree.insert("", "end", values=("Quick Ratio", quick_ratio))
        tree.insert("", "end", values=("Debt-Equity Ratio", debt_equity))

    def show_import_from_excel(self):
        from tkinter import filedialog
        file = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not file:
            return
        import pandas as pd
        try:
            df = pd.read_excel(file)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read Excel: {e}")
            return
        # For demo: just show the first few rows
        top = tk.Toplevel(self.root)
        top.title("Imported Excel Preview")
        txt = tk.Text(top, width=120, height=20)
        txt.pack()
        txt.insert("end", df.head().to_string())
        tk.Button(top, text="Close", command=top.destroy).pack(pady=4)

    # --- Utility: Get all ledgers and groups for dropdowns/autocomplete ---
    def get_ledgers(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT account_name FROM Ledger")
        ledgers = [row[0] for row in c.fetchall()]
        conn.close()
        return ledgers

    def get_groups(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS Groups (group_name TEXT PRIMARY KEY)")
        c.execute("SELECT group_name FROM Groups")

        groups = [row[0] for row in c.fetchall()]
        conn.close()
        return groups

# --- Accounting System: Tkinter + SQLite ---
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd

def export_to_excel(table, filename):
    try:
        cols = [table.heading(col)['text'] for col in table['columns']]
        data = [table.item(i)['values'] for i in table.get_children()]
        df = pd.DataFrame(data, columns=cols)
        df.to_excel(filename, index=False)
        messagebox.showinfo("Export", f"Data exported to {filename}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export: {e}")


# --- Accounting System: Tkinter + SQLite ---
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "accounting.db"

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Drop and recreate Journal table to ensure correct columns
    c.execute('''DROP TABLE IF EXISTS Journal''')
    c.execute('''CREATE TABLE Journal (
        id INTEGER PRIMARY KEY,
        date TEXT,
        description TEXT,
        debit_account TEXT,
        debit_amount REAL,
        credit_account TEXT,
        credit_amount REAL,
        gst_rate REAL,
        gst_type TEXT,
        cgst REAL,
        sgst REAL,
        igst REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Ledger (
        account_name TEXT PRIMARY KEY,
        balance REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS BalanceSheet (
        id INTEGER PRIMARY KEY,
        category TEXT,
        account_name TEXT,
        amount REAL
    )''')
    conn.commit()
    conn.close()

def calculate_gst(amount, gst_rate, transaction_type):
    gst_amount = (gst_rate / 100) * amount
    if transaction_type == 'intra':
        cgst = sgst = gst_amount / 2
        igst = 0
    else:
        cgst = sgst = 0
        igst = gst_amount
    return cgst, sgst, igst


# --- Improved AccountingApp with Modern Tkinter Styling ---
class AccountingApp:
    def setup_trial_balance_tab(self):
        f = ttk.Frame(self.trial_tab, style="TFrame")
        f.pack(padx=30, pady=20, anchor="n")
        ttk.Label(f, text="Trial Balance as on Today").pack(anchor="w")
        self.trial_tree = ttk.Treeview(self.trial_tab, columns=("Account Name", "Debit", "Credit"), show="headings", height=15)
        for col in self.trial_tree["columns"]:
            self.trial_tree.heading(col, text=col)
            self.trial_tree.column(col, anchor="center", width=180)
        self.trial_tree.pack(fill="both", expand=True, padx=20, pady=10)
        ttk.Button(self.trial_tab, text="Refresh", command=self.refresh_trial_balance).pack(pady=5)
        self.refresh_trial_balance()

    def refresh_trial_balance(self):
        for i in self.trial_tree.get_children():
            self.trial_tree.delete(i)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT account_name, balance FROM Ledger")
        rows = c.fetchall()
        conn.close()
        total_debit = total_credit = 0
        for acct, bal in rows:
            if bal >= 0:
                self.trial_tree.insert("", "end", values=(acct, bal, ""))
                total_debit += bal
            else:
                self.trial_tree.insert("", "end", values=(acct, "", -bal))
                total_credit += -bal
        self.trial_tree.insert("", "end", values=("TOTAL", total_debit, total_credit))

    def setup_pl_tab(self):
        f = ttk.Frame(self.pl_tab, style="TFrame")
        f.pack(padx=30, pady=20, anchor="n")
        ttk.Label(f, text="Profit & Loss Statement (Demo)").pack(anchor="w")
        self.pl_tree = ttk.Treeview(self.pl_tab, columns=("Type", "Account Name", "Amount"), show="headings", height=15)
        for col in self.pl_tree["columns"]:
            self.pl_tree.heading(col, text=col)
            self.pl_tree.column(col, anchor="center", width=180)
        self.pl_tree.pack(fill="both", expand=True, padx=20, pady=10)
        ttk.Button(self.pl_tab, text="Refresh", command=self.refresh_pl).pack(pady=5)
        self.refresh_pl()

    def refresh_pl(self):
        for i in self.pl_tree.get_children():
            self.pl_tree.delete(i)
        # Demo: Show all income/expense from Journal (real logic would use account types)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT debit_account, debit_amount FROM Journal WHERE debit_account LIKE '%expense%' OR debit_account LIKE '%cost%'")
        expenses = c.fetchall()
        c.execute("SELECT credit_account, credit_amount FROM Journal WHERE credit_account LIKE '%income%' OR credit_account LIKE '%revenue%'")
        incomes = c.fetchall()
        conn.close()
        total_income = sum(x[1] for x in incomes)
        total_expense = sum(x[1] for x in expenses)
        for acct, amt in incomes:
            self.pl_tree.insert("", "end", values=("Income", acct, amt))
        for acct, amt in expenses:
            self.pl_tree.insert("", "end", values=("Expense", acct, amt))
        self.pl_tree.insert("", "end", values=("Net Profit/Loss", "", total_income - total_expense))

    def setup_gst_tab(self):
        f = ttk.Frame(self.gst_tab, style="TFrame")
        f.pack(padx=30, pady=20, anchor="n")
        ttk.Label(f, text="GST/Tax Summary").pack(anchor="w")
        self.gst_tree = ttk.Treeview(self.gst_tab, columns=("Type", "Amount"), show="headings", height=10)
        for col in self.gst_tree["columns"]:
            self.gst_tree.heading(col, text=col)
            self.gst_tree.column(col, anchor="center", width=180)
        self.gst_tree.pack(fill="both", expand=True, padx=20, pady=10)
        ttk.Button(self.gst_tab, text="Refresh", command=self.refresh_gst).pack(pady=5)
        self.refresh_gst()

    def refresh_gst(self):
        for i in self.gst_tree.get_children():
            self.gst_tree.delete(i)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT SUM(cgst), SUM(sgst), SUM(igst) FROM Journal")
        cgst, sgst, igst = c.fetchone()
        conn.close()
        self.gst_tree.insert("", "end", values=("CGST", cgst or 0))
        self.gst_tree.insert("", "end", values=("SGST", sgst or 0))
        self.gst_tree.insert("", "end", values=("IGST", igst or 0))

    def export_ledger_csv(self):
        import csv
        from tkinter import filedialog
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file:
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT account_name, balance FROM Ledger")
        rows = c.fetchall()
        conn.close()
        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Account Name", "Balance"])
            writer.writerows(rows)
        messagebox.showinfo("Export", f"Ledger exported to {file}")

    def backup_database(self):
        import shutil
        from tkinter import filedialog
        file = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
        if not file:
            return
        shutil.copy(DB_NAME, file)
        messagebox.showinfo("Backup", f"Database backed up to {file}")

    def restore_database(self):
        import shutil
        from tkinter import filedialog
        file = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if not file:
            return
        shutil.copy(file, DB_NAME)
        messagebox.showinfo("Restore", f"Database restored from {file}\nPlease restart the application.")
    def __init__(self, root):
        self.root = root
        self.root.title("Tally-like Accounting System")
        self.root.geometry("1400x850")
        self.root.configure(bg="#FFF8E1")

        # --- Tally Color Scheme ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#FFF8E1")
        style.configure("TLabel", background="#FFF8E1", foreground="#222", font=("Segoe UI", 12))
        style.configure("TButton", background="#1976D2", foreground="#fff", font=("Segoe UI", 11, "bold"), borderwidth=0, padding=[12, 8], relief="flat")
        style.map("TButton", background=[("active", "#1565C0")], foreground=[("active", "#fff")])
        style.configure("Treeview", background="#FFFDE7", foreground="#222", fieldbackground="#FFFDE7", font=("Segoe UI", 11), rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background="#FFD600", foreground="#222", font=("Segoe UI", 12, "bold"), borderwidth=0)
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        # --- Left Navigation (Tally Gateway) ---
        nav_frame = tk.Frame(self.root, bg="#FFD600", width=260)
        nav_frame.pack(side="left", fill="y")
        nav_label = tk.Label(nav_frame, text="Gateway of Accounting", bg="#FFD600", fg="#222", font=("Segoe UI", 18, "bold"), pady=18)
        nav_label.pack(fill="x")
        nav_btns = [
            ("Masters", self.show_masters),
            ("Vouchers", self.show_vouchers),
            ("Day Book", self.show_daybook),
            ("Reports", self.show_reports),
            ("Utilities", self.show_utilities),
        ]
        for text, cmd in nav_btns:
            b = tk.Button(nav_frame, text=text, bg="#FFD600", fg="#222", font=("Segoe UI", 14, "bold"), bd=0, relief="flat", activebackground="#FFF9C4", activeforeground="#1976D2", cursor="hand2", command=cmd)
            b.pack(fill="x", pady=2, padx=10)

        # --- Main Content Area ---
        self.content_frame = tk.Frame(self.root, bg="#FFF8E1")
        self.content_frame.pack(side="left", fill="both", expand=True)
        self.show_gateway()

        # --- Info Panel (Bottom) ---
        self.info_panel = tk.Label(self.root, text="F1: Help | F2: Date | F4: Contra | F5: Payment | F6: Receipt | F7: Journal | F8: Sales | F9: Purchase | Alt+G: Go To", bg="#FFD600", fg="#222", font=("Segoe UI", 11), anchor="w")
        self.info_panel.pack(side="bottom", fill="x")

        # --- Keyboard Shortcuts ---
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F2>', lambda e: self.select_date())
        self.root.bind('<F4>', lambda e: self.show_voucher_type('Contra'))
        self.root.bind('<F5>', lambda e: self.show_voucher_type('Payment'))
        self.root.bind('<F6>', lambda e: self.show_voucher_type('Receipt'))
        self.root.bind('<F7>', lambda e: self.show_voucher_type('Journal'))
        self.root.bind('<F8>', lambda e: self.show_voucher_type('Sales'))
        self.root.bind('<F9>', lambda e: self.show_voucher_type('Purchase'))
        self.root.bind('<Alt-g>', lambda e: self.show_goto())

    # --- Gateway/Home ---
    def show_gateway(self):
        self.clear_content()
        lbl = tk.Label(self.content_frame, text="Welcome to Tally-like Accounting System\nSelect a module from the left menu.", font=("Segoe UI", 20, "bold"), bg="#FFF8E1", fg="#1976D2", pady=40)
        lbl.pack(expand=True)

    # --- Navigation Handlers ---
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_masters(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Masters (Ledgers, Groups)", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        # Ledgers Section
        ledgers_frame = tk.LabelFrame(self.content_frame, text="Ledgers", bg="#FFF8E1", fg="#1976D2", font=("Segoe UI", 14, "bold"), padx=10, pady=10)
        ledgers_frame.pack(side="left", fill="y", padx=20, pady=10)
        tk.Label(ledgers_frame, text="Name:", bg="#FFF8E1").grid(row=0, column=0, sticky="w")
        self.ledger_name_var = tk.StringVar()
        ledger_names = self.get_ledgers()
        self.ledger_name_combo = ttk.Combobox(ledgers_frame, textvariable=self.ledger_name_var, values=ledger_names, width=18)
        self.ledger_name_combo.grid(row=0, column=1)
        tk.Label(ledgers_frame, text="Group:", bg="#FFF8E1").grid(row=1, column=0, sticky="w")
        self.ledger_group_var = tk.StringVar()
        group_names = self.get_groups()
        self.ledger_group_combo = ttk.Combobox(ledgers_frame, textvariable=self.ledger_group_var, values=group_names, width=18)
        self.ledger_group_combo.grid(row=1, column=1)
        tk.Label(ledgers_frame, text="Opening Balance:", bg="#FFF8E1").grid(row=2, column=0, sticky="w")
        self.ledger_opening_var = tk.StringVar()
        tk.Entry(ledgers_frame, textvariable=self.ledger_opening_var, width=20).grid(row=2, column=1)
        tk.Button(ledgers_frame, text="Create/Update Ledger", command=self.create_update_ledger, width=18).grid(row=3, column=0, columnspan=2, pady=6)
        tk.Button(ledgers_frame, text="Delete Ledger", command=self.delete_ledger, width=18).grid(row=4, column=0, columnspan=2, pady=6)
        # List Ledgers
        self.ledgers_tree = ttk.Treeview(ledgers_frame, columns=("Name", "Group", "Balance"), show="headings", height=8)
        for col in ("Name", "Group", "Balance"):
            self.ledgers_tree.heading(col, text=col)
            self.ledgers_tree.column(col, anchor="center", width=120)
        self.ledgers_tree.grid(row=5, column=0, columnspan=2, pady=8)
        self.ledgers_tree.bind("<ButtonRelease-1>", self.on_ledger_select)
        self.refresh_ledgers_tree()

        # Groups Section
        groups_frame = tk.LabelFrame(self.content_frame, text="Groups", bg="#FFF8E1", fg="#1976D2", font=("Segoe UI", 14, "bold"), padx=10, pady=10)
        groups_frame.pack(side="left", fill="y", padx=20, pady=10)
        tk.Label(groups_frame, text="Group Name:", bg="#FFF8E1").grid(row=0, column=0, sticky="w")
        self.group_name_var = tk.StringVar()
        group_names2 = self.get_groups()
        self.group_name_combo = ttk.Combobox(groups_frame, textvariable=self.group_name_var, values=group_names2, width=18)
        self.group_name_combo.grid(row=0, column=1)
        tk.Button(groups_frame, text="Create Group", command=self.create_group, width=18).grid(row=1, column=0, columnspan=2, pady=6)
        # List Groups
        self.groups_tree = ttk.Treeview(groups_frame, columns=("Group Name",), show="headings", height=8)
        self.groups_tree.heading("Group Name", text="Group Name")
        self.groups_tree.column("Group Name", anchor="center", width=140)
        self.groups_tree.grid(row=2, column=0, columnspan=2, pady=8)
        self.refresh_groups_tree()

    def create_update_ledger(self):
        name = self.ledger_name_var.get().strip()
        group = self.ledger_group_var.get().strip()
        try:
            opening = float(self.ledger_opening_var.get().strip())
        except Exception:
            opening = 0.0
        if not name or not group:
            messagebox.showerror("Input Error", "Ledger name and group are required.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO Ledger (account_name, balance) VALUES (?, ?)", (name, opening))
        # For demo, just store group in a separate table
        c.execute("CREATE TABLE IF NOT EXISTS Groups (group_name TEXT PRIMARY KEY)")
        c.execute("INSERT OR IGNORE INTO Groups (group_name) VALUES (?)", (group,))
        conn.commit()
        conn.close()
        self.refresh_ledgers_tree()
        self.refresh_groups_tree()
        messagebox.showinfo("Success", f"Ledger '{name}' saved.")

    def delete_ledger(self):
        name = self.ledger_name_var.get().strip()
        if not name:
            messagebox.showerror("Input Error", "Select a ledger to delete.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM Ledger WHERE account_name=?", (name,))
        conn.commit()
        conn.close()
        self.refresh_ledgers_tree()
        messagebox.showinfo("Deleted", f"Ledger '{name}' deleted.")

    def on_ledger_select(self, event):
        sel = self.ledgers_tree.selection()
        if sel:
            vals = self.ledgers_tree.item(sel[0])['values']
            self.ledger_name_var.set(vals[0])
            self.ledger_group_var.set(vals[1])
            self.ledger_opening_var.set(vals[2])

    def refresh_ledgers_tree(self):
        for i in getattr(self, 'ledgers_tree', []).get_children() if hasattr(self, 'ledgers_tree') else []:
            self.ledgers_tree.delete(i)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT account_name, '' as group_name, balance FROM Ledger")
        for row in c.fetchall():
            self.ledgers_tree.insert("", "end", values=row)
        conn.close()

    def create_group(self):
        name = self.group_name_var.get().strip()
        if not name:
            messagebox.showerror("Input Error", "Group name required.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS Groups (group_name TEXT PRIMARY KEY)")
        c.execute("INSERT OR IGNORE INTO Groups (group_name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        self.refresh_groups_tree()
        messagebox.showinfo("Success", f"Group '{name}' saved.")

    def refresh_groups_tree(self):
        for i in getattr(self, 'groups_tree', []).get_children() if hasattr(self, 'groups_tree') else []:
            self.groups_tree.delete(i)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS Groups (group_name TEXT PRIMARY KEY)")
        c.execute("SELECT group_name FROM Groups")
        for row in c.fetchall():
            self.groups_tree.insert("", "end", values=row)
        conn.close()

    def show_vouchers(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Vouchers (All Types)", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        for vtype in ["Contra", "Payment", "Receipt", "Journal", "Sales", "Purchase", "Debit Note", "Credit Note"]:
            tk.Button(self.content_frame, text=f"{vtype} Voucher", command=lambda vt=vtype: self.show_voucher_type(vt), width=18).pack(pady=4)

    def show_voucher_type(self, vtype):
        self.clear_content()
        tk.Label(self.content_frame, text=f"{vtype} Voucher Entry", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        form = tk.Frame(self.content_frame, bg="#FFF8E1")
        form.pack(pady=10)
        # Fetch ledgers/groups for dropdowns
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT account_name FROM Ledger")
        ledgers = [row[0] for row in c.fetchall()]
        c.execute("CREATE TABLE IF NOT EXISTS Groups (group_name TEXT PRIMARY KEY)")
        c.execute("SELECT group_name FROM Groups")
        groups = [row[0] for row in c.fetchall()]
        conn.close()
        # Common fields
        tk.Label(form, text="Date (YYYY-MM-DD):", bg="#FFF8E1").grid(row=0, column=0, sticky="w")
        date_var = tk.StringVar()
        tk.Entry(form, textvariable=date_var, width=18).grid(row=0, column=1)
        tk.Label(form, text="Description:", bg="#FFF8E1").grid(row=1, column=0, sticky="w")
        desc_var = tk.StringVar()
        tk.Entry(form, textvariable=desc_var, width=30).grid(row=1, column=1, columnspan=2)
        # Debit/Credit fields with dropdowns
        tk.Label(form, text="Debit Account:", bg="#FFF8E1").grid(row=2, column=0, sticky="w")
        debit_var = tk.StringVar()
        debit_combo = ttk.Combobox(form, textvariable=debit_var, values=ledgers, width=16)
        debit_combo.grid(row=2, column=1)
        tk.Label(form, text="Debit Amount:", bg="#FFF8E1").grid(row=2, column=2, sticky="w")
        debit_amt_var = tk.StringVar()
        tk.Entry(form, textvariable=debit_amt_var, width=12).grid(row=2, column=3)
        tk.Label(form, text="Credit Account:", bg="#FFF8E1").grid(row=3, column=0, sticky="w")
        credit_var = tk.StringVar()
        credit_combo = ttk.Combobox(form, textvariable=credit_var, values=ledgers, width=16)
        credit_combo.grid(row=3, column=1)
        tk.Label(form, text="Credit Amount:", bg="#FFF8E1").grid(row=3, column=2, sticky="w")
        credit_amt_var = tk.StringVar()
        tk.Entry(form, textvariable=credit_amt_var, width=12).grid(row=3, column=3)
        # GST fields (for Sales/Purchase)
        gst_rate_var = tk.StringVar(value="0")
        gst_type_var = tk.StringVar(value="intra")
        if vtype in ("Sales", "Purchase"):
            tk.Label(form, text="GST Rate (%):", bg="#FFF8E1").grid(row=4, column=0, sticky="w")
            tk.Entry(form, textvariable=gst_rate_var, width=8).grid(row=4, column=1)
            tk.Label(form, text="GST Type (intra/inter):", bg="#FFF8E1").grid(row=4, column=2, sticky="w")
            gst_type_combo = ttk.Combobox(form, textvariable=gst_type_var, values=["intra", "inter"], width=8)
            gst_type_combo.grid(row=4, column=3)
        # Add Button
        def add_voucher():
            try:
                date = date_var.get().strip()
                desc = desc_var.get().strip()
                debit_acct = debit_var.get().strip()
                debit_amt = float(debit_amt_var.get().strip())
                credit_acct = credit_var.get().strip()
                credit_amt = float(credit_amt_var.get().strip())
                gst_rate = float(gst_rate_var.get().strip()) if vtype in ("Sales", "Purchase") else 0.0
                gst_type = gst_type_var.get().strip() if vtype in ("Sales", "Purchase") else ""
                if not (date and desc and debit_acct and credit_acct):
                    raise ValueError("All fields required.")
                cgst, sgst, igst = calculate_gst(debit_amt, gst_rate, gst_type) if vtype in ("Sales", "Purchase") else (0, 0, 0)
            except Exception as e:
                messagebox.showerror("Input Error", f"Invalid input: {e}")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''INSERT INTO Journal (date, description, debit_account, debit_amount, credit_account, credit_amount, gst_rate, gst_type, cgst, sgst, igst)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (date, desc, debit_acct, debit_amt, credit_acct, credit_amt, gst_rate, gst_type, cgst, sgst, igst))
            # Update Ledger
            c.execute('''INSERT INTO Ledger (account_name, balance) VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET balance = balance + excluded.balance''', (debit_acct, debit_amt))
            c.execute('''INSERT INTO Ledger (account_name, balance) VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET balance = balance - ?''', (credit_acct, credit_amt, credit_amt))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"{vtype} voucher added.")
        tk.Button(form, text="Add Voucher", command=add_voucher, width=18).grid(row=6, column=0, columnspan=4, pady=10)

        # List of Vouchers (summary)
        tree = ttk.Treeview(self.content_frame, columns=("Date", "Desc", "Debit", "Debit Amt", "Credit", "Credit Amt"), show="headings", height=8)
        for i, col in enumerate(("Date", "Desc", "Debit", "Debit Amt", "Credit", "Credit Amt")):
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=120 if i!=1 else 200)
        tree.pack(pady=10)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT date, description, debit_account, debit_amount, credit_account, credit_amount FROM Journal ORDER BY id DESC LIMIT 20")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    def show_daybook(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Day Book (All Vouchers)", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        # Filter bar
        filter_frame = tk.Frame(self.content_frame, bg="#FFF8E1")
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="From (YYYY-MM-DD):", bg="#FFF8E1").pack(side="left")
        from_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=from_var, width=12).pack(side="left", padx=2)
        tk.Label(filter_frame, text="To (YYYY-MM-DD):", bg="#FFF8E1").pack(side="left")
        to_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=to_var, width=12).pack(side="left", padx=2)
        tk.Label(filter_frame, text="Search:", bg="#FFF8E1").pack(side="left", padx=(10,0))
        search_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=search_var, width=16).pack(side="left", padx=2)
        # Table
        columns = ("Date", "Desc", "Debit", "Debit Amt", "Credit", "Credit Amt")
        tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", height=14)
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=120 if i!=1 else 200)
        tree.pack(pady=10, fill="x")
        def refresh_daybook():
            for i in tree.get_children():
                tree.delete(i)
            query = "SELECT date, description, debit_account, debit_amount, credit_account, credit_amount FROM Journal WHERE 1=1"
            params = []
            if from_var.get().strip():
                query += " AND date >= ?"
                params.append(from_var.get().strip())
            if to_var.get().strip():
                query += " AND date <= ?"
                params.append(to_var.get().strip())
            if search_var.get().strip():
                s = f"%{search_var.get().strip()}%"
                query += " AND (description LIKE ? OR debit_account LIKE ? OR credit_account LIKE ?)"
                params += [s, s, s]
            query += " ORDER BY date DESC, id DESC"
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            for row in c.execute(query, params):
                tree.insert("", "end", values=row)
            conn.close()
        tk.Button(filter_frame, text="Filter", command=refresh_daybook, width=10).pack(side="left", padx=8)
        # Export to Excel button
        def export_daybook():
            from tkinter import filedialog
            file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if file:
                self.export_to_excel(tree, file)
        tk.Button(self.content_frame, text="Export to Excel", command=export_daybook, width=16).pack(pady=2)
        refresh_daybook()


    def show_reports(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Reports", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        reports = [
            ("Balance Sheet", lambda: self.show_report_type("Balance Sheet")),
            ("Profit & Loss", lambda: self.show_report_type("Profit & Loss")),
            ("Trial Balance", lambda: self.show_report_type("Trial Balance")),
            ("GST/Tax Summary", lambda: self.show_report_type("GST/Tax Summary")),
            ("Ledger Report", lambda: self.show_report_type("Ledger Report")),
            ("Cash Flow Statement", self.show_cash_flow_report),
            ("Ratio Analysis", self.show_ratio_analysis_report),
            ("Import from Excel", self.show_import_from_excel),
        ]
        for rpt, func in reports:
            tk.Button(self.content_frame, text=rpt, command=func, width=18).pack(pady=4)

    def show_report_type(self, rpt):
        self.clear_content()
        tk.Label(self.content_frame, text=f"{rpt}", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        if rpt == "Balance Sheet":
            # Summarized Balance Sheet
            tree = ttk.Treeview(self.content_frame, columns=("Category", "Account Name", "Amount"), show="headings", height=14)
            for col in ("Category", "Account Name", "Amount"):
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=180)
            tree.pack(pady=10, fill="x")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT category, account_name, amount FROM BalanceSheet")
            for row in c.fetchall():
                tree.insert("", "end", values=row)
            conn.close()
        elif rpt == "Profit & Loss":
            # Summarized P&L
            tree = ttk.Treeview(self.content_frame, columns=("Type", "Account Name", "Amount"), show="headings", height=14)
            for col in ("Type", "Account Name", "Amount"):
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=180)
            tree.pack(pady=10, fill="x")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT debit_account, debit_amount FROM Journal WHERE debit_account LIKE '%expense%' OR debit_account LIKE '%cost%'")
            expenses = c.fetchall()
            c.execute("SELECT credit_account, credit_amount FROM Journal WHERE credit_account LIKE '%income%' OR credit_account LIKE '%revenue%'")
            incomes = c.fetchall()
            conn.close()
            total_income = sum(x[1] for x in incomes)
            total_expense = sum(x[1] for x in expenses)
            for acct, amt in incomes:
                tree.insert("", "end", values=("Income", acct, amt))
            for acct, amt in expenses:
                tree.insert("", "end", values=("Expense", acct, amt))
            tree.insert("", "end", values=("Net Profit/Loss", "", total_income - total_expense))
        elif rpt == "Trial Balance":
            # Summarized Trial Balance
            tree = ttk.Treeview(self.content_frame, columns=("Account Name", "Debit", "Credit"), show="headings", height=14)
            for col in ("Account Name", "Debit", "Credit"):
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=180)
            tree.pack(pady=10, fill="x")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT account_name, balance FROM Ledger")
            rows = c.fetchall()
            conn.close()
            total_debit = total_credit = 0
            for acct, bal in rows:
                if bal >= 0:
                    tree.insert("", "end", values=(acct, bal, ""))
                    total_debit += bal
                else:
                    tree.insert("", "end", values=(acct, "", -bal))
                    total_credit += -bal
            tree.insert("", "end", values=("TOTAL", total_debit, total_credit))
        elif rpt == "GST/Tax Summary":
            # GST/Tax Summary
            tree = ttk.Treeview(self.content_frame, columns=("Type", "Amount"), show="headings", height=10)
            for col in ("Type", "Amount"):
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=180)
            tree.pack(pady=10, fill="x")
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT SUM(cgst), SUM(sgst), SUM(igst) FROM Journal")
            cgst, sgst, igst = c.fetchone()
            conn.close()
            tree.insert("", "end", values=("CGST", cgst or 0))
            tree.insert("", "end", values=("SGST", sgst or 0))
            tree.insert("", "end", values=("IGST", igst or 0))
        elif rpt == "Ledger Report":
            # Ledger-wise report
            filter_frame = tk.Frame(self.content_frame, bg="#FFF8E1")
            filter_frame.pack(pady=5)
            tk.Label(filter_frame, text="Ledger Name:", bg="#FFF8E1").pack(side="left")
            ledger_var = tk.StringVar()
            tk.Entry(filter_frame, textvariable=ledger_var, width=18).pack(side="left", padx=2)
            def show_ledger():
                for i in tree.get_children():
                    tree.delete(i)
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT date, description, debit_account, debit_amount, credit_account, credit_amount FROM Journal WHERE debit_account=? OR credit_account=? ORDER BY date DESC", (ledger_var.get().strip(), ledger_var.get().strip()))
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
                conn.close()
            tk.Button(filter_frame, text="Show", command=show_ledger, width=10).pack(side="left", padx=8)
            tree = ttk.Treeview(self.content_frame, columns=("Date", "Desc", "Debit", "Debit Amt", "Credit", "Credit Amt"), show="headings", height=14)
            for i, col in enumerate(("Date", "Desc", "Debit", "Debit Amt", "Credit", "Credit Amt")):
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=120 if i!=1 else 200)
            tree.pack(pady=10, fill="x")
        else:
            tk.Label(self.content_frame, text="(Report details here)", bg="#FFF8E1").pack(pady=10)

    def show_utilities(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Utilities", font=("Segoe UI", 18, "bold"), bg="#FFF8E1", fg="#1976D2").pack(pady=20)
        tk.Button(self.content_frame, text="Export Data", command=self.export_ledger_csv, width=18).pack(pady=6)
        tk.Button(self.content_frame, text="Backup DB", command=self.backup_database, width=18).pack(pady=6)
        tk.Button(self.content_frame, text="Restore DB", command=self.restore_database, width=18).pack(pady=6)

    def show_help(self):
        messagebox.showinfo("Help", "Tally-like Accounting System\n\n- Use the left menu or keyboard shortcuts.\n- F4: Contra, F5: Payment, F6: Receipt, F7: Journal, F8: Sales, F9: Purchase, etc.\n- Alt+G: Go To any module.\n- Masters: Manage Ledgers, Groups, Stock, GST.\n- Vouchers: Enter all types of transactions.\n- Reports: View all financial reports.\n- Utilities: Export, Backup, Restore.")

    def select_date(self):
        messagebox.showinfo("Date", "Date selection coming soon (Tally-style period filter)")

    def show_goto(self):
        messagebox.showinfo("Go To", "Go To (Alt+G): Quickly jump to any module. Coming soon!")

    # --- Masters Placeholders ---
    def create_ledger(self):
        messagebox.showinfo("Create Ledger", "Ledger creation form coming soon!")
    def alter_ledger(self):
        messagebox.showinfo("Alter Ledger", "Ledger alteration form coming soon!")
    def delete_ledger(self):
        messagebox.showinfo("Delete Ledger", "Ledger deletion coming soon!")

    def show_search_info(self, event=None):
        # Comprehensive info database
        info_db = {
            "entity concept": "Entity Concept: The business is treated as a separate entity from its owners.",
            "going concern": "Going Concern: The business will continue to operate for the foreseeable future.",
            "money measurement": "Money Measurement: Only transactions measurable in money are recorded.",
            "cost principle": "Cost Principle: Assets are recorded at their original cost.",
            "dual aspect": "Dual Aspect: Every transaction affects at least two accounts (double entry).",
            "accrual concept": "Accrual Concept: Revenues and expenses are recognized when they occur, not when cash is exchanged.",
            "matching principle": "Matching Principle: Expenses are matched with related revenues in the same period.",
            "conservatism": "Conservatism: Anticipate losses but not gains.",
            "consistency": "Consistency: Use the same accounting methods from period to period.",
            "materiality": "Materiality: All significant information must be reported.",
            "schedule iii": "Schedule III: Companies must prepare balance sheets as per Schedule III of the Companies Act, 2013.",
            "gst": "GST: Goods and Services Tax is a value-added tax on most goods and services sold for domestic consumption in India.",
            "gst rate": "GST Rate: The percentage of GST applicable to a transaction, as per government notification.",
            "cgst": "CGST: Central Goods and Services Tax, levied by the Central Government.",
            "sgst": "SGST: State Goods and Services Tax, levied by the State Government.",
            "igst": "IGST: Integrated Goods and Services Tax, levied on inter-state transactions.",
            "income tax": "Income Tax: Tax levied on the income of individuals and businesses as per the Income Tax Act, 1961.",
            "tds": "TDS: Tax Deducted at Source, a means of collecting income tax in India.",
            "audit": "Audit: Examination of financial records to ensure accuracy and compliance.",
            "books of account": "Books of Account: Records maintained for all financial transactions as per law.",
            "balance sheet": "Balance Sheet: Statement showing assets, liabilities, and equity at a specific date.",
            "profit and loss": "Profit & Loss Statement: Shows revenues, expenses, and profit/loss for a period.",
            "trial balance": "Trial Balance: List of all ledger accounts and their balances at a point in time.",
            "tax compliance": "Tax Compliance: Adhering to all tax laws, including timely filing of returns and payment of taxes.",
            "accounting standards": "Accounting Standards: Rules and guidelines for preparing financial statements (e.g., Ind AS, IFRS).",
            "ind as": "Ind AS: Indian Accounting Standards, converged with IFRS.",
            "ifrs": "IFRS: International Financial Reporting Standards.",
            "companies act": "Companies Act: The law governing companies in India, including accounting and reporting requirements.",
            "income tax act": "Income Tax Act: The law governing income tax in India.",
            "double entry": "Double Entry: Every transaction is recorded in at least two accounts, ensuring the accounting equation balances.",
            "depreciation": "Depreciation: Systematic allocation of the cost of an asset over its useful life.",
            "amortization": "Amortization: Gradual write-off of intangible assets.",
            "inventory valuation": "Inventory Valuation: Methods include FIFO, LIFO, and Weighted Average.",
            "audit trail": "Audit Trail: A step-by-step record by which accounting data can be traced to its source.",
            "compliance": "Compliance: Following all applicable laws, standards, and regulations.",
            # Add more as needed
        }
        query = self.search_var.get().strip().lower()
        if not query:
            messagebox.showinfo("Search Accounting Info", "Enter a keyword (e.g., 'GST', 'Schedule III', 'Income Tax', 'Entity Concept', etc.)")
            return
        # Find best match (simple contains search)
        results = []
        for k, v in info_db.items():
            if query in k or query in v.lower():
                results.append(f"{k.title()}:\n{v}")
        if not results:
            messagebox.showinfo("Search Result", f"No information found for '{query}'. Try another keyword.")
        else:
            messagebox.showinfo("Search Result", "\n\n".join(results))

        # --- Notebook Tabs ---
        self.tab_control = ttk.Notebook(self.root, style="TNotebook")
        self.journal_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.ledger_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.balance_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.trial_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.pl_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.gst_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.tab_control.add(self.journal_tab, text="\U0001F4C3 Journal")
        self.tab_control.add(self.ledger_tab, text="\U0001F4CA Ledger")
        self.tab_control.add(self.balance_tab, text="\U0001F4B0 Balance Sheet")
        self.tab_control.add(self.trial_tab, text="\U0001F4C8 Trial Balance")
        self.tab_control.add(self.pl_tab, text="\U0001F4B8 Profit && Loss")
        self.tab_control.add(self.gst_tab, text="\U0001F4B5 GST/Tax Summary")
        self.tab_control.pack(expand=1, fill="both", padx=18, pady=(0, 10))

        # --- Setup Tabs ---
        self.setup_journal_tab()
        self.setup_ledger_tab()
        self.setup_balance_tab()
        self.setup_trial_balance_tab()
        self.setup_pl_tab()
        self.setup_gst_tab()

        # --- Utility Buttons ---
        util_frame = ttk.Frame(self.root, style="TFrame")
        util_frame.pack(pady=8)
        ttk.Button(util_frame, text="Export Ledger to CSV", command=self.export_ledger_csv).pack(side="left", padx=8)
        ttk.Button(util_frame, text="Backup DB", command=self.backup_database).pack(side="left", padx=8)
        ttk.Button(util_frame, text="Restore DB", command=self.restore_database).pack(side="left", padx=8)

        # --- Footer ---
        footer = tk.Label(self.root, text="\u00A9 2025 Advanced Accounting | Modern UI | Powered by Tkinter & SQLite", bg="#181c24", fg="#00D1FF", font=("Segoe UI", 10), anchor="e")
        footer.pack(side="bottom", fill="x", pady=(0, 2), padx=10)

    def setup_journal_tab(self):
        f = ttk.Frame(self.journal_tab, style="TFrame")
        f.pack(padx=30, pady=20, anchor="n")
        labels = [
            "Date (YYYY-MM-DD)", "Description", "Debit Account", "Debit Amount",
            "Credit Account", "Credit Amount", "GST Rate (%)", "GST Type (intra/inter)"
        ]
        self.entries = []
        for i, label in enumerate(labels):
            ttk.Label(f, text=label+':').grid(row=i, column=0, sticky="w", pady=3)
            e = ttk.Entry(f, width=30)
            e.grid(row=i, column=1, pady=3)
            self.entries.append(e)
        self.add_entry_btn = ttk.Button(f, text="Add Entry", command=self.add_journal_entry)
        self.add_entry_btn.grid(row=len(labels), column=0, columnspan=2, pady=12)

        # Journal Treeview with Edit/Delete
        self.journal_tree = ttk.Treeview(self.journal_tab, columns=("ID","Date","Desc","Debit Acct","Debit Amt","Credit Acct","Credit Amt","GST Rate","GST Type","CGST","SGST","IGST"), show="headings", height=10)
        for col in self.journal_tree["columns"]:
            self.journal_tree.heading(col, text=col)
            self.journal_tree.column(col, anchor="center", width=90)
        self.journal_tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Edit/Delete Buttons
        btn_frame = ttk.Frame(self.journal_tab)
        btn_frame.pack(pady=5)
        self.refresh_journal_btn = ttk.Button(btn_frame, text="Refresh", command=self.refresh_journal)
        self.refresh_journal_btn.pack(side="left", padx=5)
        self.edit_btn = ttk.Button(btn_frame, text="Edit Selected", command=self.edit_selected_journal)
        self.edit_btn.pack(side="left", padx=5)
        self.delete_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected_journal)
        self.delete_btn.pack(side="left", padx=5)
        self.refresh_journal()  # Ensure table is populated on start

    def edit_selected_journal(self):
        selected = self.journal_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a journal entry to edit.")
            return
        item = self.journal_tree.item(selected[0])
        values = item['values']
        # Fill entry fields with selected values (skip ID)
        for i, e in enumerate(self.entries):
            e.delete(0, tk.END)
            e.insert(0, values[i+1])
        # Store ID for update
        self.editing_id = values[0]
        self.add_entry_btn.config(text="Update Entry", command=self.update_journal_entry)

    def update_journal_entry(self):
        try:
            date, desc, debit_acct, debit_amt, credit_acct, credit_amt, gst_rate, gst_type = [e.get().strip() for e in self.entries]
            if not (date and desc and debit_acct and debit_amt and credit_acct and credit_amt and gst_rate and gst_type):
                raise ValueError("All fields are required.")
            debit_amt = float(debit_amt)
            credit_amt = float(credit_amt)
            gst_rate = float(gst_rate)
            if gst_type.lower() not in ("intra", "inter"):
                raise ValueError("GST Type must be 'intra' or 'inter'.")
            cgst, sgst, igst = calculate_gst(debit_amt, gst_rate, gst_type.lower())
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            # Get old values for ledger reversal
            c.execute("SELECT debit_account, debit_amount, credit_account, credit_amount FROM Journal WHERE id=?", (self.editing_id,))
            old = c.fetchone()
            if old:
                old_debit_acct, old_debit_amt, old_credit_acct, old_credit_amt = old
                # Reverse old ledger
                c.execute('''UPDATE Ledger SET balance = balance - ? WHERE account_name = ?''', (old_debit_amt, old_debit_acct))
                c.execute('''UPDATE Ledger SET balance = balance + ? WHERE account_name = ?''', (old_credit_amt, old_credit_acct))
            # Update journal
            c.execute('''UPDATE Journal SET date=?, description=?, debit_account=?, debit_amount=?, credit_account=?, credit_amount=?, gst_rate=?, gst_type=?, cgst=?, sgst=?, igst=? WHERE id=?''',
                (date, desc, debit_acct, debit_amt, credit_acct, credit_amt, gst_rate, gst_type.lower(), cgst, sgst, igst, self.editing_id))
            # Update ledger with new values
            c.execute('''INSERT INTO Ledger (account_name, balance) VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET balance = balance + excluded.balance''', (debit_acct, debit_amt))
            c.execute('''INSERT INTO Ledger (account_name, balance) VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET balance = balance - ?''', (credit_acct, credit_amt, credit_amt))
            conn.commit()
            conn.close()
            self.refresh_journal()
            self.refresh_ledger()
            for e in self.entries:
                e.delete(0, tk.END)
            self.add_entry_btn.config(text="Add Entry", command=self.add_journal_entry)
            messagebox.showinfo("Success", "Journal entry updated.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not update entry: {e}")

    def delete_selected_journal(self):
        selected = self.journal_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a journal entry to delete.")
            return
        item = self.journal_tree.item(selected[0])
        values = item['values']
        entry_id = values[0]
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            # Get old values for ledger reversal
            c.execute("SELECT debit_account, debit_amount, credit_account, credit_amount FROM Journal WHERE id=?", (entry_id,))
            old = c.fetchone()
            if old:
                old_debit_acct, old_debit_amt, old_credit_acct, old_credit_amt = old
                # Reverse old ledger
                c.execute('''UPDATE Ledger SET balance = balance - ? WHERE account_name = ?''', (old_debit_amt, old_debit_acct))
                c.execute('''UPDATE Ledger SET balance = balance + ? WHERE account_name = ?''', (old_credit_amt, old_credit_acct))
            # Delete journal entry
            c.execute("DELETE FROM Journal WHERE id=?", (entry_id,))
            conn.commit()
            conn.close()
            self.refresh_journal()
            self.refresh_ledger()
            messagebox.showinfo("Success", "Journal entry deleted.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not delete entry: {e}")

    def setup_ledger_tab(self):
        f = ttk.Frame(self.ledger_tab, style="TFrame")
        f.pack(padx=30, pady=20, anchor="n")
        self.ledger_tree = ttk.Treeview(self.ledger_tab, columns=("Account Name", "Balance"), show="headings", height=12)
        for col in self.ledger_tree["columns"]:
            self.ledger_tree.heading(col, text=col)
            self.ledger_tree.column(col, anchor="center", width=180)
        self.ledger_tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_ledger_btn = ttk.Button(self.ledger_tab, text="Refresh", command=self.refresh_ledger)
        self.refresh_ledger_btn.pack(pady=5)
        self.refresh_ledger()

    def setup_balance_tab(self):
        f = ttk.Frame(self.balance_tab, style="TFrame")
        f.pack(padx=30, pady=20, anchor="n")
        # Dropdown for organization type
        org_types = ["Firm", "Individual", "Company"]
        self.org_type_var = tk.StringVar(value=org_types[0])
        ttk.Label(f, text="Select Organization Type:").grid(row=0, column=0, sticky="w", pady=3)
        org_menu = ttk.OptionMenu(f, self.org_type_var, org_types[0], *org_types, command=lambda _: self.refresh_balance())
        org_menu.grid(row=0, column=1, sticky="w", pady=3)

        self.balance_tree = ttk.Treeview(self.balance_tab, columns=("Category", "Account Name", "Amount"), show="headings", height=12)
        for col in self.balance_tree["columns"]:
            self.balance_tree.heading(col, text=col)
            self.balance_tree.column(col, anchor="center", width=180)
        self.balance_tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_balance_btn = ttk.Button(self.balance_tab, text="Refresh", command=self.refresh_balance)
        self.refresh_balance_btn.pack(pady=5)
        self.refresh_balance()

        # Add button to show accounting principles/compliance
        ttk.Button(self.balance_tab, text="Accounting Principles & Compliance", command=self.show_compliance_info).pack(pady=5)

    def show_compliance_info(self):
        info = (
            "Key Accounting Principles:\n"
            "- Entity Concept\n"
            "- Going Concern\n"
            "- Money Measurement\n"
            "- Cost Principle\n"
            "- Dual Aspect (Double Entry)\n"
            "- Accrual Concept\n"
            "- Matching Principle\n"
            "- Conservatism\n"
            "- Consistency\n"
            "- Materiality\n\n"
            "Compliance Reminders:\n"
            "- Maintain proper documentation for all entries.\n"
            "- Ensure GST and tax calculations are as per latest law.\n"
            "- For companies, follow Schedule III of Companies Act for balance sheet.\n"
            "- For firms/individuals, follow standard formats as per Income Tax Act.\n"
            "- Always use double-entry for every transaction.\n"
        )
        messagebox.showinfo("Accounting Principles & Compliance", info)

    def add_journal_entry(self):
        try:
            date, desc, debit_acct, debit_amt, credit_acct, credit_amt, gst_rate, gst_type = [e.get().strip() for e in self.entries]
            if not (date and desc and debit_acct and debit_amt and credit_acct and credit_amt and gst_rate and gst_type):
                raise ValueError("All fields are required.")
            debit_amt = float(debit_amt)
            credit_amt = float(credit_amt)
            gst_rate = float(gst_rate)
            if gst_type.lower() not in ("intra", "inter"):
                raise ValueError("GST Type must be 'intra' or 'inter'.")
            cgst, sgst, igst = calculate_gst(debit_amt, gst_rate, gst_type.lower())
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''INSERT INTO Journal (date, description, debit_account, debit_amount, credit_account, credit_amount, gst_rate, gst_type, cgst, sgst, igst)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (date, desc, debit_acct, debit_amt, credit_acct, credit_amt, gst_rate, gst_type.lower(), cgst, sgst, igst))
            # Update Ledger
            # Debit increases balance, Credit decreases balance
            c.execute('''INSERT INTO Ledger (account_name, balance) VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET balance = balance + excluded.balance''', (debit_acct, debit_amt))
            c.execute('''INSERT INTO Ledger (account_name, balance) VALUES (?, ?)
                ON CONFLICT(account_name) DO UPDATE SET balance = balance - ?''', (credit_acct, credit_amt, credit_amt))
            conn.commit()
            conn.close()
            self.refresh_journal()
            self.refresh_ledger()
            for e in self.entries:
                e.delete(0, tk.END)
            messagebox.showinfo("Success", "Journal entry added.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not add entry: {e}")

    def refresh_journal(self):
        for i in self.journal_tree.get_children():
            self.journal_tree.delete(i)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, date, description, debit_account, debit_amount, credit_account, credit_amount, gst_rate, gst_type, cgst, sgst, igst FROM Journal")
        for row in c.fetchall():
            self.journal_tree.insert("", "end", values=row)
        conn.close()

    def refresh_ledger(self):
        for i in self.ledger_tree.get_children():
            self.ledger_tree.delete(i)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT account_name, balance FROM Ledger")
        for row in c.fetchall():
            self.ledger_tree.insert("", "end", values=row)
        conn.close()

    def refresh_balance(self):
        for i in self.balance_tree.get_children():
            self.balance_tree.delete(i)
        org_type = self.org_type_var.get().lower()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT category, account_name, amount FROM BalanceSheet")
        rows = c.fetchall()
        conn.close()
        # Group and order rows according to org type
        schedule = self.get_balance_sheet_schedule(org_type, rows)
        for row in schedule:
            self.balance_tree.insert("", "end", values=row)

    def get_balance_sheet_schedule(self, org_type, rows):
        # Group and order rows as per org type
        if org_type == "company":
            # Schedule III (abridged):
            order = [
                "Share Capital", "Reserves & Surplus", "Non-Current Liabilities", "Current Liabilities",
                "Non-Current Assets", "Current Assets"
            ]
        elif org_type == "firm":
            order = [
                "Capital", "Drawings", "Loans", "Current Liabilities", "Fixed Assets", "Current Assets"
            ]
        else:  # individual
            order = [
                "Capital", "Drawings", "Loans", "Assets", "Liabilities"
            ]
        # Group rows by category
        grouped = {cat: [] for cat in order}
        for cat, acct, amt in rows:
            if cat in grouped:
                grouped[cat].append((cat, acct, amt))
            else:
                grouped.setdefault("Other", []).append((cat, acct, amt))
        # Flatten in order
        schedule = []
        for cat in order:
            schedule.extend(grouped.get(cat, []))
        schedule.extend(grouped.get("Other", []))
        return schedule

if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    app = AccountingApp(root)
    root.mainloop()
