import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

DB = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "shopsight")
}

def connect():
    return mysql.connector.connect(**DB)

def setup():
    c = mysql.connector.connect(
        host=DB["host"], port=DB["port"],
        user=DB["user"], password=DB["password"]
    )
    q = c.cursor()
    q.execute("CREATE DATABASE IF NOT EXISTS shopsight")
    q.close()
    c.close()

    c = connect()
    q = c.cursor()

    q.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    q.execute("""
        CREATE TABLE IF NOT EXISTS businesses(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNIQUE NOT NULL,
            name VARCHAR(150) NOT NULL,
            type VARCHAR(100) NOT NULL,
            years INT DEFAULT 0,
            currency VARCHAR(10) DEFAULT 'INR',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    q.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(150) NOT NULL,
            cost DECIMAL(12,2) NOT NULL,
            price DECIMAL(12,2) NOT NULL,
            quantity INT NOT NULL,
            stock INT NOT NULL,
            expiry DATE NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    q.execute("""
        CREATE TABLE IF NOT EXISTS sales(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            product_name VARCHAR(150) NOT NULL,
            units INT NOT NULL,
            price DECIMAL(12,2) NOT NULL,
            cost DECIMAL(12,2) NOT NULL,
            sale_date DATE NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    c.commit()
    q.close()
    c.close()


class ShopSight:
    def __init__(self, root):
        self.root = root
        self.root.title("ShopSight")
        self.root.geometry("1050x700")
        self.root.configure(bg="#0f172a")
        self.user_id = None
        self.business = None
        self.login()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def heading(self, text):
        tk.Label(
            self.root,
            text=text,
            bg="#0f172a",
            fg="white",
            font=("Arial", 25, "bold")
        ).pack(pady=20)

    def entry(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=parent["bg"],
            fg="#cbd5e1"
        ).pack(anchor="w")

        e = tk.Entry(
            parent,
            bg="#0f172a",
            fg="white",
            insertbackground="white",
            relief="flat"
        )
        e.pack(fill="x", ipady=7, pady=(3, 10))
        return e

    def button(self, parent, text, command):
        tk.Button(
            parent,
            text=text,
            command=command,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=8
        ).pack(pady=5)

    def login(self):
        self.clear()

        box = tk.Frame(
            self.root,
            bg="#1e293b",
            padx=35,
            pady=30
        )
        box.place(
            relx=.5,
            rely=.5,
            anchor="center",
            width=390
        )

        tk.Label(
            box,
            text="ShopSight",
            bg="#1e293b",
            fg="#60a5fa",
            font=("Arial", 28, "bold")
        ).pack(pady=(0, 8))

        tk.Label(
            box,
            text="Smarter decisions for your shop",
            bg="#1e293b",
            fg="#94a3b8"
        ).pack(pady=(0, 20))

        email = self.entry(box, "Email")
        password = self.entry(box, "Password")
        password.config(show="*")

        def login():
            try:
                c = connect()
                q = c.cursor(dictionary=True)

                q.execute(
                    "SELECT * FROM users WHERE email=%s",
                    (email.get().strip().lower(),)
                )

                user = q.fetchone()
                q.close()
                c.close()

                if not user or not check_password_hash(
                    user["password"], password.get()
                ):
                    messagebox.showerror(
                        "Login Failed",
                        "Incorrect email or password."
                    )
                    return

                self.user_id = user["id"]
                self.business = self.get_business()

                if self.business:
                    self.dashboard()
                else:
                    self.onboarding()

            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        self.button(box, "Login", login)
        self.button(box, "Create Account", self.signup)

    def signup(self):
        self.clear()

        box = tk.Frame(
            self.root,
            bg="#1e293b",
            padx=35,
            pady=25
        )
        box.place(
            relx=.5,
            rely=.5,
            anchor="center",
            width=400
        )

        tk.Label(
            box,
            text="Create Account",
            bg="#1e293b",
            fg="#60a5fa",
            font=("Arial", 23, "bold")
        ).pack(pady=(0, 15))

        name = self.entry(box, "Full Name")
        email = self.entry(box, "Email")
        password = self.entry(box, "Password")
        confirm = self.entry(box, "Confirm Password")

        password.config(show="*")
        confirm.config(show="*")

        def create():
            name_value = name.get().strip()
            email_value = email.get().strip().lower()
            password_value = password.get()

            if not name_value or not email_value:
                messagebox.showerror("Error", "Fill in all fields.")
                return

            if len(password_value) < 6:
                messagebox.showerror(
                    "Error",
                    "Password must have at least 6 characters."
                )
                return

            if password_value != confirm.get():
                messagebox.showerror(
                    "Error",
                    "Passwords do not match."
                )
                return

            try:
                c = connect()
                q = c.cursor()

                q.execute(
                    """
                    INSERT INTO users(name,email,password)
                    VALUES(%s,%s,%s)
                    """,
                    (
                        name_value,
                        email_value,
                        generate_password_hash(password_value)
                    )
                )

                self.user_id = q.lastrowid
                c.commit()

                q.close()
                c.close()

                self.onboarding()

            except mysql.connector.IntegrityError:
                messagebox.showerror(
                    "Error",
                    "An account with this email already exists."
                )

            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        self.button(box, "Create Account", create)
        self.button(box, "Back to Login", self.login)

    def get_business(self):
        c = connect()
        q = c.cursor(dictionary=True)

        q.execute(
            "SELECT * FROM businesses WHERE user_id=%s",
            (self.user_id,)
        )

        business = q.fetchone()

        q.close()
        c.close()

        return business

    def onboarding(self):
        self.clear()

        box = tk.Frame(
            self.root,
            bg="#1e293b",
            padx=35,
            pady=25
        )
        box.place(
            relx=.5,
            rely=.5,
            anchor="center",
            width=430
        )

        tk.Label(
            box,
            text="Business Setup",
            bg="#1e293b",
            fg="#60a5fa",
            font=("Arial", 23, "bold")
        ).pack(pady=(0, 15))

        name = self.entry(box, "Business Name")
        business_type = self.entry(box, "Business Type")
        years = self.entry(box, "Years in Operation")
        currency = self.entry(box, "Currency")

        currency.insert(0, "INR")

        def save():
            try:
                name_value = name.get().strip()
                type_value = business_type.get().strip()
                years_value = int(years.get() or 0)
                currency_value = currency.get().strip().upper()

                if not name_value or not type_value:
                    raise ValueError

                if years_value < 0:
                    raise ValueError

                if not currency_value:
                    raise ValueError

                c = connect()
                q = c.cursor()

                q.execute(
                    """
                    INSERT INTO businesses
                    (user_id,name,type,years,currency)
                    VALUES(%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user_id,
                        name_value,
                        type_value,
                        years_value,
                        currency_value
                    )
                )

                c.commit()
                q.close()
                c.close()

                self.business = self.get_business()
                self.dashboard()

            except Exception:
                messagebox.showerror(
                    "Error",
                    "Enter valid business details."
                )

        self.button(box, "Save and Continue", save)

    def menu(self):
        bar = tk.Frame(self.root, bg="#111827")
        bar.pack(fill="x")

        buttons = [
            ("Dashboard", self.dashboard),
            ("Inventory", self.inventory),
            ("Sales", self.sales),
            ("Analytics", self.analytics),
            ("Logout", self.logout)
        ]

        for text, command in buttons:
            tk.Button(
                bar,
                text=text,
                command=command,
                bg="#1e293b",
                fg="white",
                activebackground="#2563eb",
                activeforeground="white",
                relief="flat",
                padx=14,
                pady=8
            ).pack(side="left", padx=3, pady=7)

    def dashboard(self):
        self.clear()
        self.menu()
        self.heading("Business Dashboard")

        c = connect()
        q = c.cursor()

        q.execute(
            """
            SELECT
            COALESCE(SUM(units*price),0),
            COALESCE(SUM((price-cost)*units),0),
            COALESCE(SUM(units),0)
            FROM sales
            WHERE user_id=%s
            """,
            (self.user_id,)
        )

        revenue, profit, units = q.fetchone()

        q.execute(
            "SELECT COUNT(*) FROM products WHERE user_id=%s",
            (self.user_id,)
        )
        products = q.fetchone()[0]

        q.execute(
            """
            SELECT COUNT(*) FROM products
            WHERE user_id=%s AND stock<=5
            """,
            (self.user_id,)
        )
        low = q.fetchone()[0]

        q.close()
        c.close()

        tk.Label(
            self.root,
            text=f"Welcome to {self.business['name']}",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Arial", 13)
        ).pack()

        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(fill="x", padx=30, pady=30)

        cards = [
            ("Revenue", self.money(revenue)),
            ("Profit", self.money(profit)),
            ("Products", products),
            ("Low Stock", low)
        ]

        for name, value in cards:
            card = tk.Frame(
                frame,
                bg="#1e293b",
                padx=20,
                pady=20
            )
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=7
            )

            tk.Label(
                card,
                text=name,
                bg="#1e293b",
                fg="#94a3b8"
            ).pack(anchor="w")

            tk.Label(
                card,
                text=value,
                bg="#1e293b",
                fg="white",
                font=("Arial", 19, "bold")
            ).pack(anchor="w", pady=8)

        if low:
            tk.Label(
                self.root,
                text=f"Warning: {low} product(s) have low stock.",
                bg="#0f172a",
                fg="#f87171",
                font=("Arial", 12, "bold")
            ).pack(pady=10)

        tk.Label(
            self.root,
            text=f"Total units sold: {units}",
            bg="#0f172a",
            fg="#94a3b8"
        ).pack()

    def inventory(self):
        self.clear()
        self.menu()
        self.heading("Inventory Management")

        top = tk.Frame(self.root, bg="#0f172a")
        top.pack(fill="x", padx=30)

        manual = tk.LabelFrame(
            top,
            text="Add Product Manually",
            bg="#1e293b",
            fg="white",
            padx=15,
            pady=10
        )
        manual.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )

        name = self.entry(manual, "Product Name")
        cost = self.entry(manual, "Buying Cost")
        price = self.entry(manual, "Selling Price")
        quantity = self.entry(manual, "Quantity")
        expiry = self.entry(manual, "Expiry Date YYYY-MM-DD")

        def add():
            try:
                product_name = name.get().strip()
                buy = float(cost.get())
                sell = float(price.get())
                qty = int(quantity.get())
                exp = expiry.get().strip() or None

                if not product_name:
                    raise ValueError

                if buy < 0 or sell < 0 or qty <= 0:
                    raise ValueError

                c = connect()
                q = c.cursor()

                q.execute(
                    """
                    INSERT INTO products
                    (user_id,name,cost,price,quantity,stock,expiry)
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user_id,
                        product_name,
                        buy,
                        sell,
                        qty,
                        qty,
                        exp
                    )
                )

                c.commit()
                q.close()
                c.close()

                messagebox.showinfo(
                    "Success",
                    "Product added successfully."
                )

                self.inventory()

            except Exception:
                messagebox.showerror(
                    "Error",
                    "Enter valid product details."
                )

        self.button(manual, "Add Product", add)

        csv_box = tk.LabelFrame(
            top,
            text="CSV Import",
            bg="#1e293b",
            fg="white",
            padx=15,
            pady=15
        )
        csv_box.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )

        tk.Label(
            csv_box,
            text="Required columns:",
            bg="#1e293b",
            fg="white"
        ).pack(anchor="w")

        tk.Label(
            csv_box,
            text="product_name, cost, price, quantity, expiry_date",
            bg="#1e293b",
            fg="#94a3b8",
            wraplength=280
        ).pack(anchor="w", pady=15)

        self.button(
            csv_box,
            "Import CSV",
            self.import_csv
        )

        tk.Label(
            self.root,
            text="Current Inventory",
            bg="#0f172a",
            fg="white",
            font=("Arial", 17, "bold")
        ).pack(
            anchor="w",
            padx=35,
            pady=(20, 5)
        )

        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=5
        )

        columns = (
            "id",
            "name",
            "cost",
            "price",
            "stock",
            "expiry"
        )

        table = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )

        headings = [
            ("id", "ID"),
            ("name", "Product"),
            ("cost", "Cost"),
            ("price", "Price"),
            ("stock", "Stock"),
            ("expiry", "Expiry")
        ]

        for col, text in headings:
            table.heading(col, text=text)
            table.column(col, width=120)

        scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=table.yview
        )

        table.configure(yscrollcommand=scroll.set)

        table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        c = connect()
        q = c.cursor()

        q.execute(
            """
            SELECT id,name,cost,price,stock,expiry
            FROM products
            WHERE user_id=%s
            ORDER BY name
            """,
            (self.user_id,)
        )

        for row in q.fetchall():
            table.insert("", "end", values=row)

        q.close()
        c.close()

    def import_csv(self):
        file = filedialog.askopenfilename(
            title="Choose CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not file:
            return

        try:
            c = connect()
            q = c.cursor()
            count = 0

            with open(
                file,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as f:

                reader = csv.DictReader(f)

                headers = [
                    x.strip().lower()
                    for x in reader.fieldnames or []
                ]

                required = [
                    "product_name",
                    "cost",
                    "price",
                    "quantity"
                ]

                if not all(x in headers for x in required):
                    raise ValueError

                for row in reader:
                    row = {
                        k.strip().lower(): v.strip()
                        for k, v in row.items()
                    }

                    name = row["product_name"]
                    cost = float(row["cost"])
                    price = float(row["price"])
                    quantity = int(row["quantity"])
                    expiry = row.get(
                        "expiry_date",
                        ""
                    ).strip() or None

                    if not name:
                        raise ValueError

                    if cost < 0 or price < 0 or quantity <= 0:
                        raise ValueError

                    q.execute(
                        """
                        INSERT INTO products
                        (user_id,name,cost,price,quantity,stock,expiry)
                        VALUES(%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            self.user_id,
                            name,
                            cost,
                            price,
                            quantity,
                            quantity,
                            expiry
                        )
                    )

                    count += 1

            c.commit()
            q.close()
            c.close()

            messagebox.showinfo(
                "CSV Import",
                f"{count} product(s) imported successfully."
            )

            self.inventory()

        except Exception:
            try:
                c.rollback()
                q.close()
                c.close()
            except:
                pass

            messagebox.showerror(
                "CSV Import",
                "CSV file is invalid."
            )

    def sales(self):
        self.clear()
        self.menu()
        self.heading("Sales Management")

        c = connect()
        q = c.cursor(dictionary=True)

        q.execute(
            """
            SELECT * FROM products
            WHERE user_id=%s AND stock>0
            ORDER BY name
            """,
            (self.user_id,)
        )

        products = q.fetchall()

        q.close()
        c.close()

        if not products:
            tk.Label(
                self.root,
                text="No products available for sale.",
                bg="#0f172a",
                fg="#94a3b8",
                font=("Arial", 13)
            ).pack(pady=40)

            return

        box = tk.Frame(
            self.root,
            bg="#1e293b",
            padx=25,
            pady=20
        )
        box.pack(
            fill="x",
            padx=100,
            pady=20
        )

        tk.Label(
            box,
            text="Select Product",
            bg="#1e293b",
            fg="white"
        ).pack(anchor="w")

        product = tk.StringVar()

        values = [
            f"{p['id']} - {p['name']} - Stock: {p['stock']}"
            for p in products
        ]

        combo = ttk.Combobox(
            box,
            textvariable=product,
            values=values,
            state="readonly"
        )
        combo.pack(
            fill="x",
            pady=8
        )

        tk.Label(
            box,
            text="Units Sold",
            bg="#1e293b",
            fg="white"
        ).pack(anchor="w")

        units = tk.Entry(
            box,
            bg="#0f172a",
            fg="white",
            insertbackground="white",
            relief="flat"
        )
        units.pack(
            fill="x",
            ipady=7,
            pady=8
        )

        def record():
            try:
                if not product.get():
                    raise ValueError

                pid = int(product.get().split()[0])
                amount = int(units.get())

                if amount <= 0:
                    raise ValueError

                c = connect()
                q = c.cursor(dictionary=True)

                q.execute(
                    """
                    SELECT * FROM products
                    WHERE id=%s AND user_id=%s
                    FOR UPDATE
                    """,
                    (pid, self.user_id)
                )

                p = q.fetchone()

                if not p or amount > p["stock"]:
                    raise ValueError

                q.execute(
                    """
                    INSERT INTO sales
                    (user_id,product_id,product_name,
                     units,price,cost,sale_date)
                    VALUES(%s,%s,%s,%s,%s,%s,CURDATE())
                    """,
                    (
                        self.user_id,
                        p["id"],
                        p["name"],
                        amount,
                        p["price"],
                        p["cost"]
                    )
                )

                q.execute(
                    """
                    UPDATE products
                    SET stock=stock-%s
                    WHERE id=%s AND user_id=%s
                    """,
                    (
                        amount,
                        p["id"],
                        self.user_id
                    )
                )

                c.commit()
                q.close()
                c.close()

                messagebox.showinfo(
                    "Sale",
                    "Sale recorded and stock updated."
                )

                self.sales()

            except Exception:
                try:
                    c.rollback()
                    q.close()
                    c.close()
                except:
                    pass

                messagebox.showerror(
                    "Sale",
                    "Invalid sale or insufficient stock."
                )

        self.button(
            box,
            "Record Sale",
            record
        )

        tk.Label(
            self.root,
            text="Recent Sales",
            bg="#0f172a",
            fg="white",
            font=("Arial", 17, "bold")
        ).pack(
            anchor="w",
            padx=30,
            pady=10
        )

        table = ttk.Treeview(
            self.root,
            columns=(
                "date",
                "product",
                "units",
                "sale",
                "profit"
            ),
            show="headings"
        )

        for col, text in [
            ("date", "Date"),
            ("product", "Product"),
            ("units", "Units"),
            ("sale", "Sale"),
            ("profit", "Profit")
        ]:
            table.heading(col, text=text)
            table.column(col, width=150)

        table.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=5
        )

        c = connect()
        q = c.cursor(dictionary=True)

        q.execute(
            """
            SELECT * FROM sales
            WHERE user_id=%s
            ORDER BY id DESC
            LIMIT 50
            """,
            (self.user_id,)
        )

        for sale in q.fetchall():
            total = float(sale["price"]) * sale["units"]

            profit = (
                float(sale["price"]) -
                float(sale["cost"])
            ) * sale["units"]

            table.insert(
                "",
                "end",
                values=(
                    sale["sale_date"],
                    sale["product_name"],
                    sale["units"],
                    self.money(total),
                    self.money(profit)
                )
            )

        q.close()
        c.close()

    def analytics(self):
        self.clear()
        self.menu()
        self.heading("Business Analytics")

        c = connect()
        q = c.cursor(dictionary=True)

        q.execute(
            """
            SELECT
            COALESCE(SUM(units*price),0) revenue,
            COALESCE(SUM((price-cost)*units),0) profit,
            COALESCE(SUM(units),0) units
            FROM sales
            WHERE user_id=%s
            """,
            (self.user_id,)
        )

        stats = q.fetchone()

        q.execute(
            """
            SELECT
            product_name,
            SUM(units) units,
            SUM((price-cost)*units) profit
            FROM sales
            WHERE user_id=%s
            GROUP BY product_id,product_name
            ORDER BY profit DESC
            """,
            (self.user_id,)
        )

        products = q.fetchall()

        q.close()
        c.close()

        frame = tk.Frame(
            self.root,
            bg="#0f172a"
        )
        frame.pack(
            fill="x",
            padx=30,
            pady=20
        )

        cards = [
            ("Revenue", self.money(stats["revenue"])),
            ("Profit", self.money(stats["profit"])),
            ("Units Sold", stats["units"])
        ]

        for name, value in cards:
            card = tk.Frame(
                frame,
                bg="#1e293b",
                padx=20,
                pady=18
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=5
            )

            tk.Label(
                card,
                text=name,
                bg="#1e293b",
                fg="#94a3b8"
            ).pack()

            tk.Label(
                card,
                text=value,
                bg="#1e293b",
                fg="white",
                font=("Arial", 19, "bold")
            ).pack(pady=8)

        tk.Label(
            self.root,
            text="Product Performance",
            bg="#0f172a",
            fg="white",
            font=("Arial", 17, "bold")
        ).pack(
            anchor="w",
            padx=30,
            pady=10
        )

        table = ttk.Treeview(
            self.root,
            columns=("product", "units", "profit"),
            show="headings"
        )

        for col, text in [
            ("product", "Product"),
            ("units", "Units Sold"),
            ("profit", "Profit")
        ]:
            table.heading(col, text=text)
            table.column(col, width=200)

        table.pack(
            fill="both",
            expand=True,
            padx=30
        )

        for p in products:
            table.insert(
                "",
                "end",
                values=(
                    p["product_name"],
                    p["units"],
                    self.money(p["profit"])
                )
            )

    def money(self, value):
        currency = self.business["currency"]
        return f"{currency} {float(value):,.2f}"

    def logout(self):
        self.user_id = None
        self.business = None
        self.login()


try:
    setup()
    root = tk.Tk()
    ShopSight(root)
    root.mainloop()
except Exception as e:
    print("Could not start ShopSight:", e)
