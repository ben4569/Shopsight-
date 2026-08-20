import csv
import customtkinter as ctk
from tkinter import filedialog,messagebox
from werkzeug.security import generate_password_hash,check_password_hash
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
from database import get_connection

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG="#0f172a"
CARD="#1e293b"

class App:
    def __init__(self,root):
        self.root=root
        self.root.title("ShopSight")
        self.root.geometry("1100x700")
        self.user=None
        self.business=None
        self.login()

    def clear(self):
        for x in self.root.winfo_children():
            x.destroy()

    def login(self):
        self.clear()

        box=ctk.CTkFrame(self.root,width=400,height=450)
        box.place(relx=.5,rely=.5,anchor="center")

        ctk.CTkLabel(box,text="ShopSight",font=("Arial",30,"bold")).pack(pady=35)
        ctk.CTkLabel(box,text="Smarter decisions for your shop").pack()

        email=ctk.CTkEntry(box,placeholder_text="Email",width=320)
        email.pack(pady=12)

        password=ctk.CTkEntry(box,placeholder_text="Password",show="*",width=320)
        password.pack(pady=12)

        def login():
            try:
                db=get_connection()
                cur=db.cursor(dictionary=True)
                cur.execute("SELECT * FROM users WHERE email=%s",(email.get().lower(),))
                user=cur.fetchone()
                cur.close()
                db.close()

                if not user or not check_password_hash(user["password"],password.get()):
                    messagebox.showerror("Login","Wrong email or password")
                    return

                self.user=user
                self.business=self.get_business()
                self.dashboard() if self.business else self.onboarding()

            except Exception as e:
                messagebox.showerror("Database Error",str(e))

        ctk.CTkButton(box,text="Login",command=login,width=320).pack(pady=12)
        ctk.CTkButton(box,text="Create Account",command=self.signup,width=320).pack(pady=5)

    def signup(self):
        self.clear()

        box=ctk.CTkFrame(self.root,width=420,height=520)
        box.place(relx=.5,rely=.5,anchor="center")

        ctk.CTkLabel(box,text="Create Account",font=("Arial",27,"bold")).pack(pady=30)

        name=ctk.CTkEntry(box,placeholder_text="Full Name",width=330)
        name.pack(pady=10)

        email=ctk.CTkEntry(box,placeholder_text="Email",width=330)
        email.pack(pady=10)

        password=ctk.CTkEntry(box,placeholder_text="Password",show="*",width=330)
        password.pack(pady=10)

        confirm=ctk.CTkEntry(box,placeholder_text="Confirm Password",show="*",width=330)
        confirm.pack(pady=10)

        def create():
            if not name.get() or not email.get() or not password.get():
                messagebox.showerror("Error","Fill all fields")
                return

            if len(password.get())<6:
                messagebox.showerror("Error","Password must have 6 characters")
                return

            if password.get()!=confirm.get():
                messagebox.showerror("Error","Passwords do not match")
                return

            try:
                db=get_connection()
                cur=db.cursor()
                cur.execute(
                    "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                    (
                        name.get().strip(),
                        email.get().strip().lower(),
                        generate_password_hash(password.get())
                    )
                )
                db.commit()
                cur.close()
                db.close()

                db=get_connection()
                cur=db.cursor(dictionary=True)
                cur.execute("SELECT * FROM users WHERE email=%s",(email.get().lower(),))
                self.user=cur.fetchone()
                cur.close()
                db.close()

                self.onboarding()

            except Exception:
                messagebox.showerror("Error","Email already exists")

        ctk.CTkButton(box,text="Create Account",command=create,width=330).pack(pady=15)
        ctk.CTkButton(box,text="Back",command=self.login,width=330).pack()

    def get_business(self):
        db=get_connection()
        cur=db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM businesses WHERE user_id=%s",
            (self.user["id"],)
        )
        data=cur.fetchone()
        cur.close()
        db.close()
        return data

    def onboarding(self):
        self.clear()

        box=ctk.CTkFrame(self.root,width=450,height=520)
        box.place(relx=.5,rely=.5,anchor="center")

        ctk.CTkLabel(box,text="Business Setup",font=("Arial",27,"bold")).pack(pady=30)

        name=ctk.CTkEntry(box,placeholder_text="Business Name",width=350)
        name.pack(pady=10)

        typ=ctk.CTkEntry(box,placeholder_text="Business Type",width=350)
        typ.pack(pady=10)

        years=ctk.CTkEntry(box,placeholder_text="Years In Operation",width=350)
        years.pack(pady=10)

        currency=ctk.CTkEntry(box,placeholder_text="Currency",width=350)
        currency.insert(0,"INR")
        currency.pack(pady=10)

        def save():
            try:
                y=int(years.get() or 0)

                if not name.get() or not typ.get() or y<0:
                    raise ValueError

                db=get_connection()
                cur=db.cursor()

                cur.execute(
                    """
                    INSERT INTO businesses
                    (user_id,name,type,years,currency)
                    VALUES(%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        name.get(),
                        typ.get(),
                        y,
                        currency.get().upper()
                    )
                )

                db.commit()
                cur.close()
                db.close()

                self.business=self.get_business()
                self.dashboard()

            except Exception:
                messagebox.showerror("Error","Enter valid details")

        ctk.CTkButton(box,text="Continue",command=save,width=350).pack(pady=20)

    def menu(self):
        bar=ctk.CTkFrame(self.root,height=60)
        bar.pack(fill="x")

        ctk.CTkLabel(
            bar,
            text="ShopSight",
            font=("Arial",22,"bold")
        ).pack(side="left",padx=20)

        for text,command in [
            ("Dashboard",self.dashboard),
            ("Inventory",self.inventory),
            ("Sales",self.sales),
            ("Analytics",self.analytics)
        ]:
            ctk.CTkButton(
                bar,text=text,command=command,
                width=110,fg_color="transparent"
            ).pack(side="left",padx=3)

        ctk.CTkButton(
            bar,text="Logout",command=self.login,
            width=90,fg_color="#991b1b"
        ).pack(side="right",padx=15)

    def dashboard(self):
        self.clear()
        self.menu()

        frame=ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both",expand=True)

        ctk.CTkLabel(
            frame,
            text="Business Dashboard",
            font=("Arial",28,"bold")
        ).pack(anchor="w",padx=25,pady=(25,5))

        ctk.CTkLabel(
            frame,
            text=f"Welcome to {self.business['name']}",
            text_color="#94a3b8"
        ).pack(anchor="w",padx=25)

        db=get_connection()
        cur=db.cursor()

        cur.execute(
            """
            SELECT
            COALESCE(SUM(units*price),0),
            COALESCE(SUM((price-cost)*units),0),
            COALESCE(SUM(units),0)
            FROM sales WHERE user_id=%s
            """,
            (self.user["id"],)
        )

        revenue,profit,units=cur.fetchone()

        cur.execute(
            "SELECT COUNT(*) FROM products WHERE user_id=%s",
            (self.user["id"],)
        )
        products=cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*) FROM products
            WHERE user_id=%s AND stock<=5
            """,
            (self.user["id"],)
        )
        low=cur.fetchone()[0]

        cur.close()
        db.close()

        cards=ctk.CTkFrame(frame,fg_color="transparent")
        cards.pack(fill="x",padx=20,pady=25)

        data=[
            ("Revenue",self.money(revenue)),
            ("Profit",self.money(profit)),
            ("Products",products),
            ("Low Stock",low)
        ]

        for name,value in data:
            box=ctk.CTkFrame(cards,fg_color=CARD)
            box.pack(side="left",fill="both",expand=True,padx=5)

            ctk.CTkLabel(
                box,text=name,text_color="#94a3b8"
            ).pack(anchor="w",padx=15,pady=(15,5))

            ctk.CTkLabel(
                box,text=value,
                font=("Arial",20,"bold")
            ).pack(anchor="w",padx=15,pady=(0,15))

        if low:
            ctk.CTkLabel(
                frame,
                text=f"Warning: {low} product(s) have low stock",
                text_color="#f87171",
                font=("Arial",14,"bold")
            ).pack(anchor="w",padx=25,pady=10)

        ctk.CTkLabel(
            frame,
            text=f"Total units sold: {units}",
            text_color="#94a3b8"
        ).pack(anchor="w",padx=25)

    def inventory(self):
        self.clear()
        self.menu()

        frame=ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both",expand=True)

        ctk.CTkLabel(
            frame,
            text="Inventory Management",
            font=("Arial",28,"bold")
        ).pack(anchor="w",padx=25,pady=25)

        add=ctk.CTkFrame(frame,fg_color=CARD)
        add.pack(fill="x",padx=25,pady=5)

        ctk.CTkLabel(
            add,text="Add Product",
            font=("Arial",19,"bold")
        ).pack(anchor="w",padx=20,pady=15)

        name=ctk.CTkEntry(add,placeholder_text="Product Name")
        name.pack(fill="x",padx=20,pady=6)

        cost=ctk.CTkEntry(add,placeholder_text="Buying Cost")
        cost.pack(fill="x",padx=20,pady=6)

        price=ctk.CTkEntry(add,placeholder_text="Selling Price")
        price.pack(fill="x",padx=20,pady=6)

        quantity=ctk.CTkEntry(add,placeholder_text="Quantity")
        quantity.pack(fill="x",padx=20,pady=6)

        expiry=ctk.CTkEntry(add,placeholder_text="Expiry YYYY-MM-DD")
        expiry.pack(fill="x",padx=20,pady=6)

        def add_product():
            try:
                n=name.get().strip()
                co=float(cost.get())
                pr=float(price.get())
                q=int(quantity.get())
                ex=expiry.get().strip() or None

                if not n or co<0 or pr<0 or q<=0:
                    raise ValueError

                db=get_connection()
                cur=db.cursor()

                cur.execute(
                    """
                    INSERT INTO products
                    (user_id,name,cost,price,quantity,stock,expiry)
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (self.user["id"],n,co,pr,q,q,ex)
                )

                db.commit()
                cur.close()
                db.close()

                messagebox.showinfo("Inventory","Product added")
                self.inventory()

            except Exception:
                messagebox.showerror("Error","Invalid product details")

        ctk.CTkButton(
            add,text="Add Product",command=add_product
        ).pack(padx=20,pady=15)

        csvbox=ctk.CTkFrame(frame,fg_color=CARD)
        csvbox.pack(fill="x",padx=25,pady=15)

        ctk.CTkLabel(
            csvbox,
            text="CSV Import",
            font=("Arial",19,"bold")
        ).pack(anchor="w",padx=20,pady=15)

        ctk.CTkLabel(
            csvbox,
            text="product_name, cost, price, quantity, expiry_date",
            text_color="#94a3b8"
        ).pack(anchor="w",padx=20)

        ctk.CTkButton(
            csvbox,text="Import CSV",command=self.import_csv
        ).pack(anchor="w",padx=20,pady=15)

        table=ctk.CTkFrame(frame,fg_color=CARD)
        table.pack(fill="both",expand=True,padx=25,pady=10)

        for i,x in enumerate(
            ["Product","Cost","Price","Stock","Expiry","Status"]
        ):
            ctk.CTkLabel(
                table,text=x,text_color="#94a3b8"
            ).grid(row=0,column=i,padx=15,pady=12,sticky="w")

        db=get_connection()
        cur=db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM products WHERE user_id=%s ORDER BY name",
            (self.user["id"],)
        )

        for r,p in enumerate(cur.fetchall(),1):
            values=[
                p["name"],
                self.money(p["cost"]),
                self.money(p["price"]),
                p["stock"],
                p["expiry"] or "-",
                "LOW" if p["stock"]<=5 else "OK"
            ]

            for i,v in enumerate(values):
                ctk.CTkLabel(
                    table,text=str(v),
                    text_color="#f87171" if v=="LOW" else "white"
                ).grid(row=r,column=i,padx=15,pady=8,sticky="w")

        cur.close()
        db.close()

    def import_csv(self):
        file=filedialog.askopenfilename(
            filetypes=[("CSV Files","*.csv")]
        )

        if not file:
            return

        try:
            db=get_connection()
            cur=db.cursor()
            count=0

            with open(
                file,"r",encoding="utf-8-sig",newline=""
            ) as f:
                reader=csv.DictReader(f)

                required=[
                    "product_name",
                    "cost",
                    "price",
                    "quantity"
                ]

                headers=[
                    x.strip().lower()
                    for x in reader.fieldnames or []
                ]

                if not all(x in headers for x in required):
                    raise ValueError

                for row in reader:
                    row={
                        k.strip().lower():v.strip()
                        for k,v in row.items()
                    }

                    n=row["product_name"]
                    co=float(row["cost"])
                    pr=float(row["price"])
                    q=int(row["quantity"])
                    ex=row.get("expiry_date") or None

                    if not n or co<0 or pr<0 or q<=0:
                        raise ValueError

                    cur.execute(
                        """
                        INSERT INTO products
                        (user_id,name,cost,price,quantity,stock,expiry)
                        VALUES(%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (self.user["id"],n,co,pr,q,q,ex)
                    )

                    count+=1

            db.commit()
            cur.close()
            db.close()

            messagebox.showinfo(
                "CSV Import",
                f"{count} products imported"
            )

            self.inventory()

        except Exception:
            try:
                db.rollback()
                cur.close()
                db.close()
            except:
                pass

            messagebox.showerror(
                "CSV Import",
                "Invalid CSV file"
            )

    def sales(self):
        self.clear()
        self.menu()

        frame=ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both",expand=True)

        ctk.CTkLabel(
            frame,
            text="Sales Management",
            font=("Arial",28,"bold")
        ).pack(anchor="w",padx=25,pady=25)

        db=get_connection()
        cur=db.cursor(dictionary=True)

        cur.execute(
            """
            SELECT * FROM products
            WHERE user_id=%s AND stock>0
            ORDER BY name
            """,
            (self.user["id"],)
        )

        products=cur.fetchall()

        cur.close()
        db.close()

        box=ctk.CTkFrame(frame,fg_color=CARD)
        box.pack(fill="x",padx=25,pady=5)

        names=[
            f"{p['id']} - {p['name']} - Stock {p['stock']}"
            for p in products
        ]

        product=ctk.CTkComboBox(
            box,
            values=names,
            width=500
        )
        product.pack(anchor="w",padx=20,pady=20)

        units=ctk.CTkEntry(
            box,
            placeholder_text="Units Sold",
            width=500
        )
        units.pack(anchor="w",padx=20,pady=10)

        def sell():
            try:
                if not product.get():
                    raise ValueError

                pid=int(product.get().split("-")[0])
                amount=int(units.get())

                if amount<=0:
                    raise ValueError

                db=get_connection()
                cur=db.cursor(dictionary=True)

                cur.execute(
                    """
                    SELECT * FROM products
                    WHERE id=%s AND user_id=%s
                    FOR UPDATE
                    """,
                    (pid,self.user["id"])
                )

                p=cur.fetchone()

                if not p or amount>p["stock"]:
                    raise ValueError

                cur.execute(
                    """
                    INSERT INTO sales
                    (user_id,product_id,product_name,units,price,cost,sale_date)
                    VALUES(%s,%s,%s,%s,%s,%s,CURDATE())
                    """,
                    (
                        self.user["id"],
                        p["id"],
                        p["name"],
                        amount,
                        p["price"],
                        p["cost"]
                    )
                )

                cur.execute(
                    """
                    UPDATE products
                    SET stock=stock-%s
                    WHERE id=%s
                    """,
                    (amount,pid)
                )

                db.commit()
                cur.close()
                db.close()

                messagebox.showinfo("Sales","Sale recorded")
                self.sales()

            except Exception:
                try:
                    db.rollback()
                    cur.close()
                    db.close()
                except:
                    pass

                messagebox.showerror(
                    "Sales",
                    "Invalid sale or insufficient stock"
                )

        ctk.CTkButton(
            box,text="Record Sale",command=sell
        ).pack(anchor="w",padx=20,pady=15)

        ctk.CTkLabel(
            frame,
            text="Recent Sales",
            font=("Arial",20,"bold")
        ).pack(anchor="w",padx=25,pady=20)

        table=ctk.CTkFrame(frame,fg_color=CARD)
        table.pack(fill="both",expand=True,padx=25)

        for i,x in enumerate(
            ["Date","Product","Units","Sale","Profit"]
        ):
            ctk.CTkLabel(
                table,text=x,text_color="#94a3b8"
            ).grid(row=0,column=i,padx=15,pady=12,sticky="w")

        db=get_connection()
        cur=db.cursor(dictionary=True)

        cur.execute(
            """
            SELECT * FROM sales
            WHERE user_id=%s
            ORDER BY id DESC LIMIT 50
            """,
            (self.user["id"],)
        )

        for r,s in enumerate(cur.fetchall(),1):
            total=float(s["price"])*s["units"]
            profit=(float(s["price"])-float(s["cost"]))*s["units"]

            values=[
                s["sale_date"],
                s["product_name"],
                s["units"],
                self.money(total),
                self.money(profit)
            ]

            for i,v in enumerate(values):
                ctk.CTkLabel(
                    table,text=str(v)
                ).grid(row=r,column=i,padx=15,pady=8,sticky="w")

        cur.close()
        db.close()

    def analytics(self):
        self.clear()
        self.menu()

        frame=ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both",expand=True)

        ctk.CTkLabel(
            frame,
            text="Business Analytics",
            font=("Arial",28,"bold")
        ).pack(anchor="w",padx=25,pady=25)

        db=get_connection()
        cur=db.cursor(dictionary=True)

        cur.execute(
            """
            SELECT
            COALESCE(SUM(units*price),0) revenue,
            COALESCE(SUM((price-cost)*units),0) profit,
            COALESCE(SUM(units),0) units
            FROM sales
            WHERE user_id=%s
            """,
            (self.user["id"],)
        )

        stats=cur.fetchone()

        cur.execute(
            """
            SELECT product_name,
                   SUM((price-cost)*units) profit
            FROM sales
            WHERE user_id=%s
            GROUP BY product_id,product_name
            ORDER BY profit DESC
            """,
            (self.user["id"],)
        )

        products=cur.fetchall()

        cur.execute(
            """
            SELECT sale_date,
                   SUM((price-cost)*units) profit
            FROM sales
            WHERE user_id=%s
            GROUP BY sale_date
            ORDER BY sale_date
            """,
            (self.user["id"],)
        )

        daily=cur.fetchall()

        cur.close()
        db.close()

        cards=ctk.CTkFrame(frame,fg_color="transparent")
        cards.pack(fill="x",padx=20,pady=10)

        for n,v in [
            ("Revenue",self.money(stats["revenue"])),
            ("Profit",self.money(stats["profit"])),
            ("Units Sold",stats["units"])
        ]:
            box=ctk.CTkFrame(cards,fg_color=CARD)
            box.pack(side="left",fill="both",expand=True,padx=5)

            ctk.CTkLabel(
                box,text=n,text_color="#94a3b8"
            ).pack(pady=(15,3))

            ctk.CTkLabel(
                box,text=str(v),
                font=("Arial",20,"bold")
            ).pack(pady=(0,15))

        charts=ctk.CTkFrame(frame,fg_color="transparent")
        charts.pack(fill="both",expand=True,padx=25,pady=20)

        self.chart(
            charts,
            "Profit By Product",
            [x["product_name"] for x in products],
            [float(x["profit"]) for x in products],
            True
        )

        self.chart(
            charts,
            "Daily Profit",
            [str(x["sale_date"]) for x in daily],
            [float(x["profit"]) for x in daily],
            False
        )

    def chart(self,parent,title,labels,values,bar):
        box=ctk.CTkFrame(parent,fg_color=CARD)
        box.pack(side="left",fill="both",expand=True,padx=5)

        ctk.CTkLabel(
            box,text=title,
            font=("Arial",18,"bold")
        ).pack(pady=10)

        fig=Figure(figsize=(5,3),dpi=90)
        ax=fig.add_subplot(111)

        if values:
            if bar:
                ax.bar(labels,values)
            else:
                ax.plot(labels,values,marker="o")

            ax.tick_params(axis="x",rotation=45)
            ax.set_ylabel(self.business["currency"])
            ax.grid(axis="y",alpha=.2)
        else:
            ax.text(.5,.5,"No sales yet",ha="center",va="center")
            ax.set_axis_off()

        fig.tight_layout()

        canvas=FigureCanvasTkAgg(fig,master=box)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True,padx=10,pady=10)

    def money(self,value):
        return f"{self.business['currency']} {float(value):,.2f}"

root=ctk.CTk()
App(root)
root.mainloop()
