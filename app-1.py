import customtkinter as ctk
import datetime
import os
import mysql.connector
from tkinter import messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image
from collections import defaultdict
import io, csv

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

TYPES_OF_BIZ = ["Grocery", "Clothing", "Electronics", "Pharmacy", "Restaurant", "Other"]
CURRENCIES = ["INR", "USD", "AED", "EUR", "GBP"]
curr = "INR"

def get_curr_str(val):
    return f"{curr} {val:,.2f}"

bg_col = "#111827"
card_col = "#1f2937"
border_col = "#374151"
input_col = "#0f172a"
text_white = "#f9fafb"
text_muted = "#9ca3af"
blue_accent = "#3b82f6"
green_accent = "#10b981"
red_accent = "#ef4444"

widths = [45, 170, 120, 110, 100, 100, 110, 110, 110]
headers = ["S. No.", "Product Name", "Purchasing Cost", "Selling Price", "Units Purchased", "Current Units", "Stock Value", "Expiry Date", "Shop"]

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "INVENTORY")

def make_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=False,
    )

def init_db():
    temp_c = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
    )
    temp_cursor = temp_c.cursor()
    safe_db_name = DB_NAME.replace("`", "``")
    temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{safe_db_name}`")
    temp_cursor.close()
    temp_c.close()

    db = make_conn()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            cost DECIMAL(10,2) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            quantity INT NOT NULL,
            expiry_date DATE NOT NULL,
            in_shop TINYINT(1) NOT NULL DEFAULT 0,
            current_units INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_products_name (name),
            INDEX idx_products_shop (in_shop)
        )
    """)
    try:
        cur.execute("ALTER TABLE products ADD COLUMN current_units INT NULL")
    except mysql.connector.Error:
        pass
    try:
        cur.execute("ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except mysql.connector.Error:
        pass
    cur.execute("UPDATE products SET current_units = quantity WHERE current_units IS NULL")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_date DATE NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            units_sold INT NOT NULL,
            sale_price DECIMAL(10,2) NOT NULL,
            unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sales_date (sale_date),
            INDEX idx_sales_product (product_name)
        )
    """)
    try:
        cur.execute("ALTER TABLE sales ADD COLUMN unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0")
    except mysql.connector.Error:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS business_profile (
            id INT AUTO_INCREMENT PRIMARY KEY,
            business_name VARCHAR(255) NOT NULL,
            business_type VARCHAR(100) NOT NULL,
            years_in_operation INT NOT NULL,
            currency VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    cur.close()
    db.close()

try:
    init_db()
except Exception as db_error:
    root = ctk.CTk()
    root.withdraw()
    messagebox.showerror(
        "MySQL Connection Error",
        "Could not connect to MySQL. Check MYSQL_HOST, MYSQL_PORT, MYSQL_USER, "
        "MYSQL_PASSWORD and MYSQL_DATABASE.\n\n" + str(db_error),
    )
    root.destroy()
    raise SystemExit(1)

def fmt_d(d):
    if isinstance(d, datetime.date):
        return d.strftime("%d/%m/%Y")
    return str(d)

def parse_d(str_val):
    s = str_val.strip()
    if not s:
        return datetime.date.today() + datetime.timedelta(days=365)
    
    for f in ["%d/%m/%Y", "%Y-%m-%d"]:
        try:
            return datetime.datetime.strptime(s, f).date()
        except Exception:
            continue
    return None

app = ctk.CTk()
app.title("Business Management System")
app.geometry("1450x860")
app.minsize(1250, 700)
app.configure(fg_color=bg_col)

side_panel = ctk.CTkFrame(app, width=230, fg_color=card_col, corner_radius=0)
side_panel.pack(side="left", fill="y")
side_panel.pack_propagate(False)

ctk.CTkFrame(app, width=1, fg_color=border_col, corner_radius=0).pack(side="left", fill="y")

main_panel = ctk.CTkFrame(app, fg_color=bg_col, corner_radius=0)
main_panel.pack(side="left", fill="both", expand=True)

views = {}
menu_btns = {}
on_refresh = {}

def switch_to(page_name):
    views[page_name].tkraise()
    if page_name in on_refresh:
        on_refresh[page_name]()
    for k, btn in menu_btns.items():
        if k == page_name:
            btn.configure(fg_color=blue_accent, text_color="white")
        else:
            btn.configure(fg_color="transparent", text_color=text_white)

app_title_lbl = ctk.CTkLabel(side_panel, text="Business\nManager", font=ctk.CTkFont(size=18, weight="bold"), text_color=text_white, justify="left")
app_title_lbl.pack(anchor="w", padx=25, pady=(30, 35))

nav = [("home", "Home"), ("inventory", "Inventory Management"), ("analysis", "Business Analysis"), ("sales", "Sales Management")]
for page_id, lbl in nav:
    b = ctk.CTkButton(side_panel, text=lbl, anchor="w", width=190, height=42, corner_radius=8, fg_color="transparent", hover_color="#4b5563", text_color=text_white, font=ctk.CTkFont(size=13, weight="bold"), command=lambda p=page_id: switch_to(p))
    b.pack(padx=20, pady=4, fill="x")
    menu_btns[page_id] = b

def setup_onboarding_ui(parent):
    box = ctk.CTkFrame(parent, fg_color=card_col, corner_radius=14, border_width=1, border_color=border_col)
    box.place(relx=0.5, rely=0.5, anchor="center")

    inner = ctk.CTkFrame(box, fg_color="transparent")
    inner.pack(padx=40, pady=35)

    ctk.CTkLabel(inner, text="Tell us about your shop", font=ctk.CTkFont(size=22, weight="bold"), text_color=text_white).pack(anchor="w")
    ctk.CTkLabel(inner, text="A few details help set up your dashboard.", font=ctk.CTkFont(size=12), text_color=text_muted).pack(anchor="w", pady=(4, 20))

    ctk.CTkLabel(inner, text="Business Name", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_white).pack(anchor="w", pady=(10, 5))
    inp_name = ctk.CTkEntry(inner, width=340, height=38, fg_color=input_col, text_color=text_white)
    inp_name.pack()

    ctk.CTkLabel(inner, text="Business Type", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_white).pack(anchor="w", pady=(10, 5))
    combo_type = ctk.CTkComboBox(inner, values=TYPES_OF_BIZ, width=340, height=38, state="readonly")
    combo_type.set(TYPES_OF_BIZ[0])
    combo_type.pack()

    ctk.CTkLabel(inner, text="Years in Operation", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_white).pack(anchor="w", pady=(10, 5))
    inp_years = ctk.CTkEntry(inner, width=340, height=38, fg_color=input_col, text_color=text_white)
    inp_years.insert(0, "0")
    inp_years.pack()

    ctk.CTkLabel(inner, text="Currency", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_white).pack(anchor="w", pady=(10, 5))
    combo_curr = ctk.CTkComboBox(inner, values=CURRENCIES, width=340, height=38, state="readonly")
    combo_curr.set(CURRENCIES[0])
    combo_curr.pack()

    err_lbl = ctk.CTkLabel(inner, text="", font=ctk.CTkFont(size=11), text_color=red_accent)
    err_lbl.pack(anchor="w", pady=(8, 0))

    def save_info():
        global curr
        n = inp_name.get().strip()
        if not n:
            err_lbl.configure(text="Business name is required.")
            return
        try:
            yrs = int(inp_years.get().strip())
            if yrs < 0:
                err_lbl.configure(text="Years cannot be negative.")
                return
        except Exception:
            err_lbl.configure(text="Years must be a number.")
            return

        db = make_conn()
        c = db.cursor()
        c.execute("SELECT id FROM business_profile ORDER BY id DESC LIMIT 1")
        existing = c.fetchone()
        if existing:
            c.execute(
                """UPDATE business_profile
                   SET business_name=%s, business_type=%s, years_in_operation=%s, currency=%s
                   WHERE id=%s""",
                (n, combo_type.get(), yrs, combo_curr.get(), existing[0]),
            )
        else:
            c.execute(
                """INSERT INTO business_profile
                   (business_name, business_type, years_in_operation, currency)
                   VALUES (%s, %s, %s, %s)""",
                (n, combo_type.get(), yrs, combo_curr.get()),
            )
        db.commit()
        c.close()
        db.close()

        curr = combo_curr.get()
        app_title_lbl.configure(text=n)
        switch_to("home")

    ctk.CTkButton(inner, text="Continue", width=340, height=40, fg_color=blue_accent, hover_color="#2563eb", font=ctk.CTkFont(size=13, weight="bold"), command=save_info).pack(pady=(20, 0))

def setup_home_ui(parent):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    wrap.place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(wrap, text="ShopSight", font=ctk.CTkFont(size=28, weight="bold"), text_color=text_white).pack(pady=(0, 8))
    ctk.CTkLabel(wrap, text="Smarter decisions for your shop", font=ctk.CTkFont(size=13), text_color=text_muted).pack()

    grid = ctk.CTkFrame(wrap, fg_color="transparent")
    grid.pack(pady=40)

    btn_cards = [("Inventory\nManagement", "inventory"), ("Business\nAnalysis", "analysis"), ("Sales\nManagement", "sales")]
    for idx, (t, p) in enumerate(btn_cards):
        ctk.CTkButton(grid, text=t, width=200, height=130, corner_radius=12, fg_color=card_col, hover_color="#4b5563", text_color=text_white, border_width=1, border_color=border_col, font=ctk.CTkFont(size=15, weight="bold"), command=lambda dest=p: switch_to(dest)).grid(row=0, column=idx, padx=12)

def setup_inventory_ui(parent):
    hdr = ctk.CTkFrame(parent, fg_color="transparent")
    hdr.pack(fill="x", padx=40, pady=(30, 15))
    ctk.CTkLabel(hdr, text="Inventory Management", font=ctk.CTkFont(size=26, weight="bold"), text_color=text_white).pack(anchor="w")

    f_card = ctk.CTkFrame(parent, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
    f_card.pack(fill="x", padx=40, pady=10)

    f_box = ctk.CTkFrame(f_card, fg_color="transparent")
    f_box.pack(fill="x", padx=20, pady=15)

    entries = {}
    cols = [("name", "Product Name", 190), ("cost", "Total Purchasing Cost", 190), ("price", "Selling Price per Unit", 190), ("qty", "Quantity", 110)]
    for i, (k, label, w) in enumerate(cols):
        ctk.CTkLabel(f_box, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=text_white).grid(row=0, column=i, sticky="w", padx=6)
        e = ctk.CTkEntry(f_box, width=w, height=36, fg_color=input_col, text_color=text_white)
        e.grid(row=1, column=i, padx=6, pady=4)
        entries[k] = e

    ctk.CTkLabel(f_box, text="Expiry Date", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_white).grid(row=0, column=4, sticky="w", padx=6)
    d_wrap = ctk.CTkFrame(f_box, fg_color="transparent")
    d_wrap.grid(row=1, column=4, padx=6)

    today = datetime.date.today()
    cb_d = ctk.CTkComboBox(d_wrap, values=[f"{d:02d}" for d in range(1, 32)], width=60, state="readonly")
    cb_m = ctk.CTkComboBox(d_wrap, values=[f"{m:02d}" for m in range(1, 13)], width=60, state="readonly")
    cb_y = ctk.CTkComboBox(d_wrap, values=[str(y) for y in range(today.year, today.year + 6)], width=80, state="readonly")

    cb_d.set(f"{today.day:02d}")
    cb_m.set(f"{today.month:02d}")
    cb_y.set(str(today.year))
    cb_d.pack(side="left", padx=2)
    cb_m.pack(side="left", padx=2)
    cb_y.pack(side="left", padx=2)

    def load_inventory_data():
        for child in list_container.winfo_children():
            child.destroy()

        conn = make_conn()
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM products ORDER BY id")
        rows = c.fetchall()
        c.close()
        conn.close()

        for idx, item in enumerate(rows, 1):
            row_frame = ctk.CTkFrame(list_container, fg_color=card_col)
            row_frame.pack(fill="x", pady=1)

            c_total = float(item["cost"])
            u_p = int(item["quantity"])
            u_c = int(item["current_units"])
            s_val = (c_total / u_p * u_c) if u_p > 0 else 0

            row_data = [str(idx), item["name"], get_curr_str(c_total), get_curr_str(float(item["price"])), str(u_p), str(u_c), get_curr_str(s_val), fmt_d(item["expiry_date"])]
            for val, w in zip(row_data, widths[:-1]):
                ctk.CTkLabel(row_frame, text=val, width=w, font=ctk.CTkFont(size=12), text_color=text_white, anchor="w").pack(side="left", padx=6, pady=8)

            in_sh = bool(item["in_shop"])
            btn_txt = "In Shop" if in_sh else "Add to Shop"
            btn_bg = "#064e3b" if in_sh else "#374151"
            btn_fg = green_accent if in_sh else text_white

            ctk.CTkButton(row_frame, text=btn_txt, width=widths[-1], height=28, fg_color=btn_bg, text_color=btn_fg, command=lambda pid=item["id"], st=in_sh: toggle_shop_flag(pid, st)).pack(side="left", padx=6)

    def toggle_shop_flag(p_id, cur_state):
        db = make_conn()
        cur = db.cursor()
        new_st = 0 if cur_state else 1
        cur.execute("UPDATE products SET in_shop = %s WHERE id = %s", (new_st, p_id))
        db.commit()
        cur.close()
        db.close()
        load_inventory_data()

    def add_new_item():
        try:
            n = entries["name"].get().strip()
            c_val = float(entries["cost"].get())
            p_val = float(entries["price"].get())
            q_val = int(entries["qty"].get())
            exp = datetime.date(int(cb_y.get()), int(cb_m.get()), int(cb_d.get()))

            if not n or c_val <= 0 or p_val <= 0 or q_val <= 0:
                messagebox.showerror("Error", "Enter a product name and positive cost, price, and quantity.")
                return
            if exp < datetime.date.today():
                messagebox.showerror("Error", "Expiry date cannot be in the past.")
                return

            db = make_conn()
            cur = db.cursor()
            try:
                cur.execute(
                    """INSERT INTO products
                       (name, cost, price, quantity, expiry_date, in_shop, current_units)
                       VALUES (%s, %s, %s, %s, %s, 0, %s)""",
                    (n, c_val, p_val, q_val, exp, q_val),
                )
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                cur.close()
                db.close()

            for entry in entries.values():
                entry.delete(0, "end")
            load_inventory_data()
        except Exception:
            messagebox.showerror("Error", "Please enter valid product details.")

    def handle_csv():
        fp = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not fp:
            return
        db = None
        cur = None
        try:
            with open(fp, "r", encoding="utf-8-sig", newline="") as f:
                rdr = csv.DictReader(f)
                if not rdr.fieldnames:
                    raise ValueError("CSV file is empty.")
                headers_in = {h.strip().lower() for h in rdr.fieldnames if h}
                required = {"product_name", "cost", "price", "quantity", "expiry_date"}
                missing = required - headers_in
                if missing:
                    raise ValueError("Missing columns: " + ", ".join(sorted(missing)))

                rows = []
                for line_no, r in enumerate(rdr, start=2):
                    cleaned = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
                    name = cleaned["product_name"]
                    cost = float(cleaned["cost"])
                    price = float(cleaned["price"])
                    qty = int(cleaned["quantity"])
                    exp_dt = parse_d(cleaned["expiry_date"])
                    if not name or cost <= 0 or price <= 0 or qty <= 0 or exp_dt is None:
                        raise ValueError(f"Invalid product data on CSV line {line_no}.")
                    rows.append((name, cost, price, qty, exp_dt, qty))

            if not rows:
                raise ValueError("CSV contains no product rows.")

            db = make_conn()
            cur = db.cursor()
            cur.executemany(
                """INSERT INTO products
                   (name, cost, price, quantity, expiry_date, in_shop, current_units)
                   VALUES (%s, %s, %s, %s, %s, 0, %s)""",
                rows,
            )
            db.commit()
            load_inventory_data()
            messagebox.showinfo("Success", f"Imported {len(rows)} product(s) successfully.")
        except Exception as e:
            if db:
                db.rollback()
            messagebox.showerror("Error", f"Failed to import CSV: {e}")
        finally:
            if cur:
                cur.close()
            if db:
                db.close()

    actions = ctk.CTkFrame(f_box, fg_color="transparent")
    actions.grid(row=2, column=0, columnspan=5, sticky="e", pady=(10, 0))
    ctk.CTkButton(actions, text="Import CSV", width=120, height=34, fg_color="#374151", command=handle_csv).pack(side="left", padx=5)
    ctk.CTkButton(actions, text="Add Product", width=130, height=34, fg_color=blue_accent, command=add_new_item).pack(side="left")
    ctk.CTkLabel(
        f_box,
        text="CSV columns: product_name, cost, price, quantity, expiry_date",
        font=ctk.CTkFont(size=10),
        text_color=text_muted,
    ).grid(row=3, column=0, columnspan=5, sticky="w", padx=6, pady=(5, 0))

    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(fill="x", padx=40, pady=(15, 5))
    ctk.CTkLabel(bar, text="Current Inventory", font=ctk.CTkFont(size=18, weight="bold"), text_color=text_white).pack(side="left")

    tbl_card = ctk.CTkFrame(parent, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
    tbl_card.pack(fill="both", expand=True, padx=40, pady=(5, 20))

    tbl_hdr = ctk.CTkFrame(tbl_card, fg_color=bg_col)
    tbl_hdr.pack(fill="x")
    for txt, w in zip(headers, widths):
        ctk.CTkLabel(tbl_hdr, text=txt, width=w, font=ctk.CTkFont(size=12, weight="bold"), text_color=text_muted, anchor="w").pack(side="left", padx=6, pady=8)

    list_container = ctk.CTkScrollableFrame(tbl_card, fg_color=card_col)
    list_container.pack(fill="both", expand=True)

    load_inventory_data()
    on_refresh["inventory"] = load_inventory_data

def setup_sales_ui(parent):
    hdr = ctk.CTkFrame(parent, fg_color="transparent")
    hdr.pack(fill="x", padx=40, pady=(25, 10))
    ctk.CTkLabel(hdr, text="Sales Management", font=ctk.CTkFont(size=26, weight="bold"), text_color=text_white).pack(anchor="w")

    sh_card = ctk.CTkFrame(parent, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
    sh_card.pack(fill="x", padx=40, pady=5)
    ctk.CTkLabel(sh_card, text="In Shop Products", font=ctk.CTkFont(size=14, weight="bold"), text_color=text_white).pack(anchor="w", padx=15, pady=8)

    sh_list = ctk.CTkScrollableFrame(sh_card, height=120, fg_color=card_col)
    sh_list.pack(fill="x", padx=15, pady=(0, 10))

    def load_shop_items():
        for w in sh_list.winfo_children():
            w.destroy()
        db = make_conn()
        c = db.cursor(dictionary=True)
        c.execute("SELECT * FROM products WHERE in_shop = 1 ORDER BY name")
        items = c.fetchall()
        c.close()
        db.close()

        for item in items:
            f = ctk.CTkFrame(sh_list, fg_color=card_col)
            f.pack(fill="x", pady=1)
            vals = [item["name"], get_curr_str(float(item["price"])), f"Stock: {item['current_units']}"]
            for val, w in zip(vals, [250, 150, 150]):
                ctk.CTkLabel(f, text=val, width=w, anchor="w", text_color=text_white).pack(side="left", padx=5, pady=4)

    s_card = ctk.CTkFrame(parent, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
    s_card.pack(fill="x", padx=40, pady=10)
    s_box = ctk.CTkFrame(s_card, fg_color="transparent")
    s_box.pack(fill="x", padx=20, pady=15)

    td = datetime.date.today()
    cb_sd = ctk.CTkComboBox(s_box, values=[f"{d:02d}" for d in range(1, 32)], width=60)
    cb_sm = ctk.CTkComboBox(s_box, values=[f"{m:02d}" for m in range(1, 13)], width=60)
    cb_sy = ctk.CTkComboBox(s_box, values=[str(y) for y in range(td.year - 1, td.year + 2)], width=80)
    cb_sd.set(f"{td.day:02d}")
    cb_sm.set(f"{td.month:02d}")
    cb_sy.set(str(td.year))

    ctk.CTkLabel(s_box, text="Date", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
    d_group = ctk.CTkFrame(s_box, fg_color="transparent")
    d_group.grid(row=1, column=0, padx=5)
    cb_sd.pack(in_=d_group, side="left")
    cb_sm.pack(in_=d_group, side="left")
    cb_sy.pack(in_=d_group, side="left")

    ctk.CTkLabel(s_box, text="Product Name", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=5)
    inp_prod = ctk.CTkEntry(s_box, width=200)
    inp_prod.grid(row=1, column=1, padx=5)

    ctk.CTkLabel(s_box, text="Units Sold", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", padx=5)
    inp_qty = ctk.CTkEntry(s_box, width=100)
    inp_qty.grid(row=1, column=2, padx=5)

    def log_sale_action():
        try:
            pname = inp_prod.get().strip()
            num_sold = int(inp_qty.get())
            sale_dt = datetime.date(int(cb_sy.get()), int(cb_sm.get()), int(cb_sd.get()))

            db = make_conn()
            cur = db.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM products WHERE LOWER(name) = LOWER(%s) AND in_shop = 1",
                (pname,),
            )
            prod = cur.fetchone()

            if not prod:
                messagebox.showerror("Error", "Product not found!")
                cur.close()
                db.close()
                return

            if num_sold > prod["current_units"]:
                messagebox.showerror("Error", f"Only {prod['current_units']} units available.")
                cur.close()
                db.close()
                return

            unit_cost = (float(prod["cost"]) / int(prod["quantity"])) if int(prod["quantity"]) else 0.0
            cur.execute(
                """INSERT INTO sales
                   (sale_date, product_name, units_sold, sale_price, unit_cost)
                   VALUES (%s, %s, %s, %s, %s)""",
                (sale_dt, prod["name"], num_sold, float(prod["price"]), unit_cost),
            )

            remaining = prod["current_units"] - num_sold
            cur.execute(
                "UPDATE products SET current_units = %s WHERE id = %s",
                (remaining, prod["id"]),
            )

            db.commit()
            cur.close()
            db.close()

            inp_prod.delete(0, "end")
            inp_qty.delete(0, "end")
            load_shop_items()
            load_sales_history()
        except Exception as e:
            if "db" in locals() and db:
                try:
                    db.rollback()
                except Exception:
                    pass
            messagebox.showerror("Error", f"Could not record sale: {e}")
        finally:
            if "cur" in locals() and cur:
                try:
                    cur.close()
                except Exception:
                    pass
            if "db" in locals() and db:
                try:
                    db.close()
                except Exception:
                    pass

    ctk.CTkButton(s_box, text="Record Sale", fg_color=blue_accent, command=log_sale_action).grid(row=1, column=3, padx=10)

    history_card = ctk.CTkFrame(parent, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
    history_card.pack(fill="both", expand=True, padx=40, pady=(5, 20))

    history_list = ctk.CTkScrollableFrame(history_card, fg_color=card_col)
    history_list.pack(fill="both", expand=True, padx=15, pady=10)

    def load_sales_history():
        for w in history_list.winfo_children():
            w.destroy()
        s_dt = datetime.date(int(cb_sy.get()), int(cb_sm.get()), int(cb_sd.get()))

        db = make_conn()
        c = db.cursor(dictionary=True)
        c.execute("SELECT * FROM sales WHERE sale_date = %s ORDER BY id", (s_dt,))
        records = c.fetchall()
        c.close()
        db.close()

        for idx, rec in enumerate(records, 1):
            r = ctk.CTkFrame(history_list, fg_color=card_col)
            r.pack(fill="x", pady=1)
            total_val = rec["units_sold"] * float(rec["sale_price"])
            vals = [str(idx), rec["product_name"], str(rec["units_sold"]), get_curr_str(float(rec["sale_price"])), get_curr_str(total_val)]
            for text_val, w in zip(vals, [50, 250, 100, 150, 150]):
                ctk.CTkLabel(r, text=text_val, width=w, anchor="w", text_color=text_white).pack(side="left", padx=5, pady=6)

    load_shop_items()
    load_sales_history()
    on_refresh["sales"] = lambda: (load_shop_items(), load_sales_history())

class AnalysisView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=bg_col)
        self.cached_images = []

        ctk.CTkLabel(self, text="Business Analysis", font=ctk.CTkFont(size=26, weight="bold"), text_color=text_white).pack(anchor="w", padx=30, pady=(20, 5))

        self.top_box = ctk.CTkFrame(self, fg_color="transparent")
        self.top_box.pack(fill="x", padx=30, pady=5)

        self.charts_area = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_area.pack(fill="both", expand=True, padx=30, pady=5)

    def refresh(self):
        db = make_conn()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT sale_date, product_name, units_sold, sale_price, unit_cost FROM sales ORDER BY sale_date"
        )
        sales_records = cur.fetchall()
        cur.close()
        db.close()


        self.data_store = []
        for s in sales_records:
            cost_ea = float(s["unit_cost"])
            rev = s["units_sold"] * float(s["sale_price"])
            total_c = s["units_sold"] * cost_ea
            self.data_store.append({
                "date": str(s["sale_date"]),
                "product": s["product_name"],
                "units": s["units_sold"],
                "revenue": rev,
                "profit": rev - total_c
            })

        self.render_stat_cards()
        self.render_charts()

    def render_stat_cards(self):
        for w in self.top_box.winfo_children():
            w.destroy()

        tot_u = sum(x["units"] for x in self.data_store)
        tot_rev = sum(x["revenue"] for x in self.data_store)
        tot_p = sum(x["profit"] for x in self.data_store)
        prod_count = len(set(x["product"] for x in self.data_store))

        cards = [
            ("Units Sold", f"{tot_u:,}", blue_accent),
            ("Total Revenue", get_curr_str(tot_rev), blue_accent),
            ("Total Profit", get_curr_str(tot_p), green_accent),
            ("Products Sold", str(prod_count), "#8b5cf6"),
        ]
        for title, value, color in cards:
            b = ctk.CTkFrame(self.top_box, fg_color=card_col, corner_radius=10, border_width=1, border_color=border_col)
            b.pack(side="left", expand=True, fill="x", padx=5)
            ctk.CTkLabel(b, text=title, font=ctk.CTkFont(size=11), text_color=text_muted).pack(anchor="w", padx=15, pady=(10, 0))
            ctk.CTkLabel(b, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=text_white).pack(anchor="w", padx=15, pady=(0, 10))

    def render_charts(self):
        for w in self.charts_area.winfo_children():
            w.destroy()
        self.cached_images.clear()

        by_date = defaultdict(float)
        for d in self.data_store:
            by_date[d["date"]] += d["profit"]

        f1 = Figure(figsize=(5, 3), dpi=100, facecolor=card_col)
        ax1 = f1.add_subplot(111, facecolor=card_col)
        d_keys = sorted(by_date.keys())
        ax1.plot(d_keys, [by_date[k] for k in d_keys], color=green_accent, marker="o")
        ax1.set_title("Profit Trend", color=text_white)
        ax1.tick_params(colors=text_muted)

        by_prod = defaultdict(float)
        for d in self.data_store:
            by_prod[d["product"]] += d["profit"]
        pos_profits = {k: v for k, v in by_prod.items() if v > 0}

        f2 = Figure(figsize=(5, 3), dpi=100, facecolor=card_col)
        ax2 = f2.add_subplot(111, facecolor=card_col)
        if pos_profits:
            ax2.pie(pos_profits.values(), labels=pos_profits.keys(), colors=[blue_accent, green_accent, "#8b5cf6", "#f59e0b", red_accent, "#06b6d4", "#ec4899"], textprops={"color": text_white})
        ax2.set_title("Profit by Product", color=text_white)

        for fig in [f1, f2]:
            canvas = FigureCanvasAgg(fig)
            canvas.draw()

            stream = io.BytesIO()
            fig.savefig(stream, format="png", facecolor=card_col)
            stream.seek(0)

            img = ctk.CTkImage(light_image=Image.open(stream), size=(500, 250))
            self.cached_images.append(img)

            holder = ctk.CTkFrame(self.charts_area, fg_color=card_col, corner_radius=10)
            holder.pack(side="left", expand=True, fill="both", padx=5)
            ctk.CTkLabel(holder, text="", image=img).pack(pady=10)

builders = [("onboarding", setup_onboarding_ui), ("home", setup_home_ui), ("inventory", setup_inventory_ui), ("sales", setup_sales_ui)]
for name, func in builders:
    f = ctk.CTkFrame(main_panel, fg_color=bg_col)
    f.place(relwidth=1, relheight=1)
    views[name] = f
    func(f)

analysis_page = AnalysisView(main_panel)
analysis_page.place(relwidth=1, relheight=1)
views["analysis"] = analysis_page
on_refresh["analysis"] = analysis_page.refresh

db_check = make_conn()
cur_check = db_check.cursor(dictionary=True)
cur_check.execute("SELECT * FROM business_profile ORDER BY id DESC LIMIT 1")
prof = cur_check.fetchone()
cur_check.close()
db_check.close()

if prof:
    curr = prof["currency"]
    app_title_lbl.configure(text=prof["business_name"])
    switch_to("home")
else:
    switch_to("onboarding")

app.mainloop()