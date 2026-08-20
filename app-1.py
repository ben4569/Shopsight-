import csv
import customtkinter as ctk
from tkinter import filedialog,messagebox,ttk
from werkzeug.security import generate_password_hash,check_password_hash
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import get_connection

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG="#0b1017"
PANEL="#151c25"
CARD="#1b2430"
BLUE="#2563eb"
GREEN="#22c55e"
RED="#ef4444"
YELLOW="#eab308"

class App:
    def __init__(self,root):
        self.root=root
        self.root.title("ShopSight")
        self.root.geometry("1250x760")
        self.root.minsize(1000,650)
        self.user=None
        self.business=None
        self.login()

    def clear(self):
        for x in self.root.winfo_children():
            x.destroy()

    def money(self,n):
        return f"{self.business['currency']} {float(n):,.2f}"

    def db(self):
        return get_connection()

    def get_business(self):
        db=self.db()
        c=db.cursor(dictionary=True)
        c.execute("SELECT * FROM businesses WHERE user_id=%s",(self.user["id"],))
        b=c.fetchone()
        c.close()
        db.close()
        return b

    def login(self):
        self.clear()

        box=ctk.CTkFrame(self.root,width=420,height=470,fg_color=PANEL)
        box.place(relx=.5,rely=.5,anchor="center")

        ctk.CTkLabel(
            box,text="◉ ShopSight",
            font=("Arial",30,"bold"),
            text_color="#22c55e"
        ).pack(pady=(45,8))

        ctk.CTkLabel(
            box,text="Business Management",
            text_color="#94a3b8"
        ).pack(pady=(0,30))

        email=ctk.CTkEntry(
            box,width=330,height=42,
            placeholder_text="Email"
        )
        email.pack(pady=8)

        password=ctk.CTkEntry(
            box,width=330,height=42,
            placeholder_text="Password",
            show="*"
        )
        password.pack(pady=8)

        def enter():
            try:
                db=self.db()
                c=db.cursor(dictionary=True)
                c.execute(
                    "SELECT * FROM users WHERE email=%s",
                    (email.get().strip().lower(),)
                )
                u=c.fetchone()
                c.close()
                db.close()

                if not u or not check_password_hash(u["password"],password.get()):
                    messagebox.showerror("Login","Incorrect email or password")
                    return

                self.user=u
                self.business=self.get_business()

                if self.business:
                    self.dashboard()
                else:
                    self.onboarding()

            except Exception as e:
                messagebox.showerror("Database Error",str(e))

        ctk.CTkButton(
            box,text="Login",
            width=330,height=42,
            command=enter
        ).pack(pady=15)

        ctk.CTkButton(
            box,text="Create Account",
            width=330,height=40,
            fg_color="#263241",
            command=self.signup
        ).pack()

    def signup(self):
        self.clear()

        box=ctk.CTkFrame(self.root,width=430,height=560,fg_color=PANEL)
        box.place(relx=.5,rely=.5,anchor="center")

        ctk.CTkLabel(
            box,text="Create Account",
            font=("Arial",27,"bold")
        ).pack(pady=35)

        name=ctk.CTkEntry(box,width=340,placeholder_text="Full Name")
        name.pack(pady=8)

        email=ctk.CTkEntry(box,width=340,placeholder_text="Email")
        email.pack(pady=8)

        password=ctk.CTkEntry(
            box,width=340,
            placeholder_text="Password",
            show="*"
        )
        password.pack(pady=8)

        confirm=ctk.CTkEntry(
            box,width=340,
            placeholder_text="Confirm Password",
            show="*"
        )
        confirm.pack(pady=8)

        def create():
            if not name.get() or not email.get() or not password.get():
                messagebox.showerror("Error","Fill all fields")
                return

            if len(password.get())<6:
                messagebox.showerror("Error","Password must contain at least 6 characters")
                return

            if password.get()!=confirm.get():
                messagebox.showerror("Error","Passwords do not match")
                return

            try:
                db=self.db()
                c=db.cursor()

                c.execute(
                    """
                    INSERT INTO users(name,email,password)
                    VALUES(%s,%s,%s)
                    """,
                    (
                        name.get().strip(),
                        email.get().strip().lower(),
                        generate_password_hash(password.get())
                    )
                )

                db.commit()
                uid=c.lastrowid
                c.close()
                db.close()

                self.user={
                    "id":uid,
                    "name":name.get().strip(),
                    "email":email.get().strip().lower()
                }

                self.onboarding()

            except Exception:
                messagebox.showerror("Error","This email already exists")

        ctk.CTkButton(
            box,text="Create Account",
            width=340,height=42,
            command=create
        ).pack(pady=18)

        ctk.CTkButton(
            box,text="Back to Login",
            width=340,
            fg_color="#263241",
            command=self.login
        ).pack()

    def onboarding(self):
        self.clear()

        box=ctk.CTkFrame(self.root,width=650,height=650,fg_color=PANEL)
        box.place(relx=.5,rely=.5,anchor="center")

        ctk.CTkLabel(
            box,text="Business Profile",
            font=("Arial",28,"bold")
        ).pack(anchor="w",padx=45,pady=(35,5))

        ctk.CTkLabel(
            box,text="Tell us about your business",
            text_color="#94a3b8"
        ).pack(anchor="w",padx=45,pady=(0,25))

        name=ctk.CTkEntry(
            box,width=560,height=40,
            placeholder_text="Business Name"
        )
        name.pack(pady=7)

        typ=ctk.CTkComboBox(
            box,width=560,height=40,
            values=["Retail","Grocery","Clothing","Electronics","Pharmacy","Restaurant","Other"]
        )
        typ.set("Retail")
        typ.pack(pady=7)

        phone=ctk.CTkEntry(
            box,width=560,height=40,
            placeholder_text="Phone Number"
        )
        phone.pack(pady=7)

        address=ctk.CTkTextbox(
            box,width=560,height=80
        )
        address.pack(pady=7)
        address.insert("1.0","Business Address")

        years=ctk.CTkEntry(
            box,width=560,height=40,
            placeholder_text="Years in Operation"
        )
        years.pack(pady=7)

        currency=ctk.CTkComboBox(
            box,width=560,height=40,
            values=["INR","USD","AED","EUR","GBP"]
        )
        currency.set("INR")
        currency.pack(pady=7)

        def save():
            try:
                y=int(years.get() or 0)

                if not name.get().strip() or y<0:
                    raise ValueError

                db=self.db()
                c=db.cursor()

                c.execute(
                    """
                    INSERT INTO businesses
                    (user_id,name,type,phone,address,years,currency)
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        name.get().strip(),
                        typ.get(),
                        phone.get().strip(),
                        address.get("1.0","end").strip(),
                        y,
                        currency.get()
                    )
                )

                db.commit()
                c.close()
                db.close()

                self.business=self.get_business()
                self.dashboard()

            except Exception:
                messagebox.showerror("Error","Enter valid business details")

        ctk.CTkButton(
            box,text="Save & Continue",
            width=560,height=42,
            command=save
        ).pack(pady=18)

    def menu(self,active):
        bar=ctk.CTkFrame(
            self.root,
            width=210,
            fg_color="#0e141c",
            corner_radius=0
        )
        bar.pack(side="left",fill="y")

        ctk.CTkLabel(
            bar,text="◉ ShopSight",
            font=("Arial",22,"bold"),
            text_color=GREEN
        ).pack(anchor="w",padx=22,pady=(28,35))

        items=[
            ("Dashboard",self.dashboard),
            ("Products",self.products),
            ("Inventory",self.inventory),
            ("Sales",self.sales),
            ("Sales History",self.history),
            ("Import CSV",self.csv_import),
            ("Business Profile",self.profile)
        ]

        for text,command in items:
            ctk.CTkButton(
                bar,
                text=text,
                anchor="w",
                height=38,
                corner_radius=7,
                fg_color="#1d2733" if text==active else "transparent",
                hover_color="#1d2733",
                command=command
            ).pack(fill="x",padx=12,pady=3)

        ctk.CTkLabel(
            bar,
            text="Need help?\nUse ShopSight to manage\nyour shop efficiently.",
            justify="left",
            text_color="#64748b",
            fg_color="#151d27",
            corner_radius=8,
            padx=12,
            pady=12
        ).pack(side="bottom",fill="x",padx=12,pady=15)

        ctk.CTkButton(
            bar,text="Sign Out",
            anchor="w",
            fg_color="transparent",
            hover_color="#3b2024",
            command=self.logout
        ).pack(side="bottom",fill="x",padx=12,pady=(0,8))

    def top(self,parent,title,sub):
        top=ctk.CTkFrame(parent,fg_color="transparent")
        top.pack(fill="x",padx=30,pady=(25,10))

        left=ctk.CTkFrame(top,fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left,text=title,
            font=("Arial",26,"bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,text=sub,
            text_color="#718096"
        ).pack(anchor="w",pady=(3,0))

        ctk.CTkLabel(
            top,
            text=self.business["name"],
            fg_color="#1b2430",
            corner_radius=8,
            padx=15,pady=8
        ).pack(side="right")

    def dashboard(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Dashboard")
        self.top(
            main,
            "Dashboard",
            "Overview of your business performance"
        )

        area=ctk.CTkScrollableFrame(
            main,fg_color="transparent"
        )
        area.pack(fill="both",expand=True,padx=15)

        db=self.db()
        c=db.cursor(dictionary=True)

        c.execute(
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
        stats=c.fetchone()

        c.execute(
            "SELECT COUNT(*) total FROM products WHERE user_id=%s",
            (self.user["id"],)
        )
        products=c.fetchone()["total"]

        c.execute(
            """
            SELECT COUNT(*) total FROM products
            WHERE user_id=%s AND stock<=5
            """,
            (self.user["id"],)
        )
        low=c.fetchone()["total"]

        c.execute(
            """
            SELECT COUNT(*) total FROM products
            WHERE user_id=%s AND stock=0
            """,
            (self.user["id"],)
        )
        out=c.fetchone()["total"]

        c.execute(
            """
            SELECT sale_date,
            SUM(units*price) revenue,
            SUM((price-cost)*units) profit,
            SUM(units) units
            FROM sales
            WHERE user_id=%s
            GROUP BY sale_date
            ORDER BY sale_date DESC
            LIMIT 14
            """,
            (self.user["id"],)
        )
        daily=list(reversed(c.fetchall()))

        c.execute(
            """
            SELECT product_name,
            SUM((price-cost)*units) profit,
            SUM(units) units
            FROM sales
            WHERE user_id=%s
            GROUP BY product_id,product_name
            ORDER BY profit DESC
            LIMIT 7
            """,
            (self.user["id"],)
        )
        product_stats=c.fetchall()

        c.execute(
            """
            SELECT category,
            SUM(units*price) revenue
            FROM sales s
            JOIN products p ON s.product_id=p.id
            WHERE s.user_id=%s
            GROUP BY category
            ORDER BY revenue DESC
            """,
            (self.user["id"],)
        )
        categories=c.fetchall()

        c.execute(
            """
            SELECT
            COALESCE(SUM(stock),0) stock,
            COUNT(*) products
            FROM products
            WHERE user_id=%s AND stock>5
            """,
            (self.user["id"],)
        )
        normal=c.fetchone()

        c.execute(
            """
            SELECT product_name,units,price,units*price total
            FROM sales
            WHERE user_id=%s
            ORDER BY id DESC
            LIMIT 6
            """,
            (self.user["id"],)
        )
        recent=c.fetchall()

        c.close()
        db.close()

        cards=ctk.CTkFrame(area,fg_color="transparent")
        cards.pack(fill="x",pady=10)

        kpis=[
            ("Total Sales",self.money(stats["revenue"]),BLUE),
            ("Total Profit",self.money(stats["profit"]),GREEN),
            ("Total Products",products,YELLOW),
            ("Low Stock Items",low,RED)
        ]

        for title,value,color in kpis:
            box=ctk.CTkFrame(
                cards,
                fg_color=CARD,
                border_width=1,
                border_color="#263241"
            )
            box.pack(side="left",fill="both",expand=True,padx=5)

            ctk.CTkLabel(
                box,text=title,
                text_color="#94a3b8"
            ).pack(anchor="w",padx=18,pady=(16,3))

            ctk.CTkLabel(
                box,text=str(value),
                font=("Arial",21,"bold")
            ).pack(anchor="w",padx=18,pady=(0,16))

        charts1=ctk.CTkFrame(area,fg_color="transparent")
        charts1.pack(fill="both",pady=8)

        self.graph(
            charts1,
            "Revenue & Profit Trend",
            [str(x["sale_date"])[5:] for x in daily],
            [
                [float(x["revenue"]) for x in daily],
                [float(x["profit"]) for x in daily]
            ],
            ["Revenue","Profit"],
            "line"
        )

        self.graph(
            charts1,
            "Profit by Product",
            [x["product_name"] for x in product_stats],
            [float(x["profit"]) for x in product_stats],
            ["Profit"],
            "bar"
        )

        charts2=ctk.CTkFrame(area,fg_color="transparent")
        charts2.pack(fill="both",pady=8)

        self.graph(
            charts2,
            "Revenue by Category",
            [x["category"] for x in categories],
            [float(x["revenue"]) for x in categories],
            ["Revenue"],
            "pie"
        )

        stock_names=["In Stock","Low Stock","Out of Stock"]
        stock_values=[
            int(normal["products"]),
            max(low-out,0),
            int(out)
        ]

        self.graph(
            charts2,
            "Stock Summary",
            stock_names,
            stock_values,
            ["Products"],
            "donut"
        )

        charts3=ctk.CTkFrame(area,fg_color="transparent")
        charts3.pack(fill="both",pady=8)

        self.graph(
            charts3,
            "Units Sold by Product",
            [x["product_name"] for x in product_stats],
            [int(x["units"]) for x in product_stats],
            ["Units"],
            "horizontal"
        )

        daily_units=[x["units"] for x in daily]

        self.graph(
            charts3,
            "Daily Units Sold",
            [str(x["sale_date"])[5:] for x in daily],
            daily_units,
            ["Units"],
            "line"
        )

        lower=ctk.CTkFrame(area,fg_color="transparent")
        lower.pack(fill="both",pady=8)

        self.dashboard_table(
            lower,
            "Top Profitable Products",
            ["Product","Quantity Sold","Total Profit"],
            [
                (
                    x["product_name"],
                    x["units"],
                    self.money(x["profit"])
                )
                for x in product_stats
            ]
        )

        self.dashboard_table(
            lower,
            "Recent Sales",
            ["Product","Quantity","Amount"],
            [
                (
                    x["product_name"],
                    x["units"],
                    self.money(x["total"])
                )
                for x in recent
            ]
        )

    def graph(self,parent,title,labels,values,names,kind):
        box=ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_width=1,
            border_color="#263241"
        )
        box.pack(side="left",fill="both",expand=True,padx=5)

        ctk.CTkLabel(
            box,text=title,
            font=("Arial",17,"bold")
        ).pack(anchor="w",padx=15,pady=(13,2))

        fig=Figure(figsize=(5,3),dpi=90)
        ax=fig.add_subplot(111)
        fig.patch.set_facecolor(CARD)
        ax.set_facecolor(CARD)

        if labels and values:
            if kind=="line":
                for i,v in enumerate(values):
                    ax.plot(
                        labels,v,
                        marker="o",
                        linewidth=2,
                        label=names[i]
                    )
                ax.legend(
                    facecolor=CARD,
                    labelcolor="white",
                    frameon=False
                )
                ax.tick_params(colors="#94a3b8",labelsize=8)

            elif kind=="bar":
                ax.bar(labels,values)
                ax.tick_params(
                    axis="x",
                    colors="#94a3b8",
                    rotation=35,
                    labelsize=8
                )
                ax.tick_params(axis="y",colors="#94a3b8")

            elif kind=="horizontal":
                ax.barh(labels,values)
                ax.tick_params(colors="#94a3b8",labelsize=8)

            elif kind=="pie":
                ax.pie(
                    values,
                    labels=labels,
                    autopct="%1.0f%%",
                    startangle=90,
                    textprops={"color":"white","fontsize":8}
                )

            elif kind=="donut":
                ax.pie(
                    values,
                    labels=labels,
                    autopct="%1.0f%%",
                    startangle=90,
                    wedgeprops={"width":.42},
                    textprops={"color":"white","fontsize":8}
                )

            ax.grid(
                axis="y",
                alpha=.15
            )

        else:
            ax.text(
                .5,.5,
                "No sales data yet",
                color="white",
                ha="center",
                va="center"
            )
            ax.set_axis_off()

        fig.tight_layout()

        canvas=FigureCanvasTkAgg(fig,master=box)
        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=8
        )

    def dashboard_table(self,parent,title,headers,rows):
        box=ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_width=1,
            border_color="#263241"
        )
        box.pack(side="left",fill="both",expand=True,padx=5)

        ctk.CTkLabel(
            box,text=title,
            font=("Arial",17,"bold")
        ).pack(anchor="w",padx=15,pady=13)

        for i,h in enumerate(headers):
            ctk.CTkLabel(
                box,text=h,
                text_color="#718096",
                font=("Arial",11,"bold")
            ).grid(
                row=1,column=i,
                padx=12,pady=8,
                sticky="w"
            )

        for r,row in enumerate(rows,2):
            for i,value in enumerate(row):
                ctk.CTkLabel(
                    box,text=str(value)
                ).grid(
                    row=r,column=i,
                    padx=12,pady=7,
                    sticky="w"
                )

    def products(self):
        self.inventory()

    def inventory(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Inventory")
        self.top(
            main,
            "Inventory Management",
            "View and manage your products"
        )

        add=ctk.CTkButton(
            main,
            text="+ Add Product",
            width=130,
            command=self.add_product
        )
        add.place(relx=.94,rely=.075,anchor="center")

        frame=ctk.CTkFrame(main,fg_color="transparent")
        frame.pack(fill="both",expand=True,padx=30,pady=20)

        db=self.db()
        c=db.cursor(dictionary=True)
        c.execute(
            """
            SELECT * FROM products
            WHERE user_id=%s
            ORDER BY name
            """,
            (self.user["id"],)
        )
        data=c.fetchall()
        c.close()
        db.close()

        self.table_style()

        tree=ttk.Treeview(
            frame,
            columns=(
                "id","product","category",
                "buy","sell","stock",
                "profit","unit","action"
            ),
            show="headings"
        )

        headings=[
            ("id","#",45),
            ("product","Product",180),
            ("category","Category",110),
            ("buy","Buying Price",100),
            ("sell","Selling Price",100),
            ("stock","Stock",80),
            ("profit","Profit/Unit",100),
            ("unit","Unit",80),
            ("action","Action",80)
        ]

        for col,text,width in headings:
            tree.heading(col,text=text)
            tree.column(col,width=width)

        for p in data:
            profit=float(p["price"])-float(p["cost"])
            tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["name"],
                    p["category"],
                    self.money(p["cost"]),
                    self.money(p["price"]),
                    p["stock"],
                    self.money(profit),
                    p["unit"],
                    "Delete"
                )
            )

        tree.pack(fill="both",expand=True)

        def delete():
            selected=tree.selection()

            if not selected:
                return

            pid=tree.item(selected[0])["values"][0]

            if not messagebox.askyesno(
                "Delete",
                "Delete this product?"
            ):
                return

            db=self.db()
            c=db.cursor()
            c.execute(
                "DELETE FROM products WHERE id=%s AND user_id=%s",
                (pid,self.user["id"])
            )
            db.commit()
            c.close()
            db.close()
            self.inventory()

        ctk.CTkButton(
            main,
            text="Delete Selected",
            fg_color="#991b1b",
            hover_color="#7f1d1d",
            command=delete
        ).pack(anchor="e",padx=30,pady=10)

    def add_product(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Inventory")
        self.top(
            main,
            "Add Product",
            "Add a new product to your inventory"
        )

        box=ctk.CTkFrame(
            main,
            fg_color=CARD,
            width=700
        )
        box.pack(fill="x",padx=60,pady=30)

        name=ctk.CTkEntry(
            box,placeholder_text="Product Name",
            height=40
        )
        name.pack(fill="x",padx=25,pady=(25,8))

        category=ctk.CTkComboBox(
            box,
            values=[
                "Grocery","Biscuits","Beverages",
                "Dairy","Personal Care","Electronics",
                "Clothing","Other"
            ],
            height=40
        )
        category.set("Grocery")
        category.pack(fill="x",padx=25,pady=8)

        buy=ctk.CTkEntry(
            box,placeholder_text="Buying Price",
            height=40
        )
        buy.pack(fill="x",padx=25,pady=8)

        sell=ctk.CTkEntry(
            box,placeholder_text="Selling Price",
            height=40
        )
        sell.pack(fill="x",padx=25,pady=8)

        stock=ctk.CTkEntry(
            box,placeholder_text="Initial Stock",
            height=40
        )
        stock.pack(fill="x",padx=25,pady=8)

        unit=ctk.CTkComboBox(
            box,
            values=["Piece","Pack","Kg","Gram","Litre","Box","Bottle"],
            height=40
        )
        unit.set("Piece")
        unit.pack(fill="x",padx=25,pady=8)

        expiry=ctk.CTkEntry(
            box,
            placeholder_text="Expiry Date YYYY-MM-DD",
            height=40
        )
        expiry.pack(fill="x",padx=25,pady=8)

        def save():
            try:
                n=name.get().strip()
                co=float(buy.get())
                pr=float(sell.get())
                q=int(stock.get())
                ex=expiry.get().strip() or None

                if not n or co<0 or pr<0 or q<0:
                    raise ValueError

                db=self.db()
                c=db.cursor()

                c.execute(
                    """
                    INSERT INTO products
                    (user_id,name,category,cost,price,
                    quantity,stock,expiry,unit)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        self.user["id"],
                        n,
                        category.get(),
                        co,
                        pr,
                        q,
                        q,
                        ex,
                        unit.get()
                    )
                )

                db.commit()
                c.close()
                db.close()

                messagebox.showinfo("Product","Product added successfully")
                self.inventory()

            except Exception:
                messagebox.showerror(
                    "Error",
                    "Enter valid product information"
                )

        ctk.CTkButton(
            box,text="Add Product",
            height=42,
            command=save
        ).pack(fill="x",padx=25,pady=25)

    def csv_import(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Import CSV")
        self.top(
            main,
            "Import Products from CSV",
            "Upload a CSV file to import multiple products"
        )

        box=ctk.CTkFrame(
            main,
            fg_color=CARD
        )
        box.pack(fill="x",padx=60,pady=30)

        ctk.CTkLabel(
            box,
            text="CSV Format",
            font=("Arial",18,"bold")
        ).pack(anchor="w",padx=25,pady=(25,8))

        ctk.CTkLabel(
            box,
            text="Name,Category,Buying Price,Selling Price,Initial Stock,Unit\nExample: Apple,Fruits,50,80,100,Piece",
            justify="left",
            text_color="#94a3b8"
        ).pack(anchor="w",padx=25,pady=5)

        file_label=ctk.CTkLabel(
            box,
            text="No file selected",
            fg_color="#111923",
            corner_radius=7,
            anchor="w",
            padx=15
        )
        file_label.pack(fill="x",padx=25,pady=20)

        selected=[None]

        def choose():
            f=filedialog.askopenfilename(
                filetypes=[("CSV Files","*.csv")]
            )
            if f:
                selected[0]=f
                file_label.configure(text=f)

        def import_file():
            if not selected[0]:
                messagebox.showwarning("CSV","Choose a CSV file first")
                return

            try:
                db=self.db()
                c=db.cursor()
                count=0

                with open(
                    selected[0],
                    "r",
                    encoding="utf-8-sig",
                    newline=""
                ) as f:
                    reader=csv.DictReader(f)

                    headers=[
                        x.strip().lower()
                        for x in reader.fieldnames or []
                    ]

                    needed=[
                        "name",
                        "category",
                        "buying price",
                        "selling price",
                        "initial stock",
                        "unit"
                    ]

                    if not all(x in headers for x in needed):
                        raise ValueError

                    for row in reader:
                        row={
                            k.strip().lower():v.strip()
                            for k,v in row.items()
                        }

                        n=row["name"]
                        cat=row["category"]
                        co=float(row["buying price"])
                        pr=float(row["selling price"])
                        q=int(row["initial stock"])
                        u=row["unit"]

                        if not n or co<0 or pr<0 or q<0:
                            raise ValueError

                        c.execute(
                            """
                            INSERT INTO products
                            (user_id,name,category,cost,price,
                            quantity,stock,unit)
                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                self.user["id"],
                                n,cat,co,pr,q,q,u
                            )
                        )

                        count+=1

                db.commit()
                c.close()
                db.close()

                messagebox.showinfo(
                    "CSV Import",
                    f"{count} products imported successfully"
                )
                self.inventory()

            except Exception:
                try:
                    db.rollback()
                    c.close()
                    db.close()
                except:
                    pass

                messagebox.showerror(
                    "CSV Import",
                    "CSV format is incorrect"
                )

        ctk.CTkButton(
            box,text="Browse",
            command=choose,
            width=120
        ).pack(anchor="w",padx=25,pady=5)

        ctk.CTkButton(
            box,text="Import Products",
            command=import_file,
            width=160
        ).pack(anchor="w",padx=25,pady=(10,25))

    def sales(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Sales")
        self.top(
            main,
            "New Sale",
            "Add a new sale. Stock will be reduced automatically."
        )

        db=self.db()
        c=db.cursor(dictionary=True)
        c.execute(
            """
            SELECT * FROM products
            WHERE user_id=%s AND stock>0
            ORDER BY name
            """,
            (self.user["id"],)
        )
        products=c.fetchall()
        c.close()
        db.close()

        box=ctk.CTkFrame(main,fg_color=CARD)
        box.pack(fill="x",padx=60,pady=20)

        names=[
            f"{p['id']} - {p['name']} (Stock: {p['stock']})"
            for p in products
        ]

        product=ctk.CTkComboBox(
            box,
            values=names or ["No products available"],
            height=42
        )

        if names:
            product.set(names[0])

        product.pack(fill="x",padx=25,pady=(25,10))

        qty=ctk.CTkEntry(
            box,
            placeholder_text="Quantity",
            height=42
        )
        qty.pack(fill="x",padx=25,pady=10)

        price_label=ctk.CTkLabel(
            box,
            text="Selling Price: -",
            anchor="w"
        )
        price_label.pack(fill="x",padx=25,pady=10)

        total_label=ctk.CTkLabel(
            box,
            text="Total Amount: 0",
            font=("Arial",18,"bold"),
            fg_color="#111923",
            corner_radius=8,
            anchor="w"
        )
        total_label.pack(fill="x",padx=25,pady=15)

        def update():
            try:
                pid=int(product.get().split("-")[0])
                p=next(x for x in products if x["id"]==pid)
                price_label.configure(
                    text=f"Selling Price: {self.money(p['price'])}"
                )

                q=int(qty.get() or 0)
                total_label.configure(
                    text=f"Total Amount: {self.money(float(p['price'])*q)}"
                )
            except:
                pass

        product.configure(command=lambda _:update())
        qty.bind("<KeyRelease>",lambda e:update())

        def sell():
            try:
                pid=int(product.get().split("-")[0])
                amount=int(qty.get())

                if amount<=0:
                    raise ValueError

                db=self.db()
                c=db.cursor(dictionary=True)

                c.execute(
                    """
                    SELECT * FROM products
                    WHERE id=%s AND user_id=%s
                    FOR UPDATE
                    """,
                    (pid,self.user["id"])
                )

                p=c.fetchone()

                if not p or p["stock"]<amount:
                    raise ValueError

                c.execute(
                    """
                    INSERT INTO sales
                    (user_id,product_id,product_name,
                    units,price,cost,sale_date)
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

                c.execute(
                    """
                    UPDATE products
                    SET stock=stock-%s
                    WHERE id=%s AND user_id=%s
                    """,
                    (amount,pid,self.user["id"])
                )

                db.commit()
                c.close()
                db.close()

                messagebox.showinfo(
                    "Sale",
                    "Sale recorded successfully"
                )
                self.sales()

            except Exception:
                try:
                    db.rollback()
                    c.close()
                    db.close()
                except:
                    pass

                messagebox.showerror(
                    "Sale",
                    "Invalid sale or insufficient stock"
                )

        ctk.CTkButton(
            box,text="Record Sale",
            height=42,
            command=sell
        ).pack(fill="x",padx=25,pady=(5,25))

    def history(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Sales History")
        self.top(
            main,
            "Sales History",
            "View all your sales"
        )

        ctk.CTkButton(
            main,
            text="Download CSV",
            command=self.export_sales
        ).pack(anchor="e",padx=30,pady=5)

        frame=ctk.CTkFrame(main,fg_color="transparent")
        frame.pack(fill="both",expand=True,padx=30,pady=15)

        db=self.db()
        c=db.cursor(dictionary=True)

        c.execute(
            """
            SELECT sale_date,product_name,units,
            price,units*price total,
            (price-cost)*units profit
            FROM sales
            WHERE user_id=%s
            ORDER BY id DESC
            """,
            (self.user["id"],)
        )

        rows=c.fetchall()
        c.close()
        db.close()

        self.table_style()

        tree=ttk.Treeview(
            frame,
            columns=(
                "date","product","quantity",
                "price","total","profit"
            ),
            show="headings"
        )

        heads=[
            ("date","Date",150),
            ("product","Product",200),
            ("quantity","Quantity",90),
            ("price","Selling Price",110),
            ("total","Total Amount",120),
            ("profit","Profit",110)
        ]

        for col,text,width in heads:
            tree.heading(col,text=text)
            tree.column(col,width=width)

        for x in rows:
            tree.insert(
                "",
                "end",
                values=(
                    x["sale_date"],
                    x["product_name"],
                    x["units"],
                    self.money(x["price"]),
                    self.money(x["total"]),
                    self.money(x["profit"])
                )
            )

        tree.pack(fill="both",expand=True)

    def export_sales(self):
        file=filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files","*.csv")]
        )

        if not file:
            return

        try:
            db=self.db()
            c=db.cursor(dictionary=True)

            c.execute(
                """
                SELECT sale_date,product_name,
                units,price,units*price total,
                (price-cost)*units profit
                FROM sales
                WHERE user_id=%s
                ORDER BY id
                """,
                (self.user["id"],)
            )

            rows=c.fetchall()
            c.close()
            db.close()

            with open(
                file,
                "w",
                newline="",
                encoding="utf-8"
            ) as f:
                writer=csv.writer(f)

                writer.writerow([
                    "Date",
                    "Product",
                    "Quantity",
                    "Selling Price",
                    "Total Amount",
                    "Profit"
                ])

                for x in rows:
                    writer.writerow([
                        x["sale_date"],
                        x["product_name"],
                        x["units"],
                        x["price"],
                        x["total"],
                        x["profit"]
                    ])

            messagebox.showinfo(
                "Export",
                "Sales history exported successfully"
            )

        except Exception as e:
            messagebox.showerror("Export",str(e))

    def profile(self):
        self.clear()

        main=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0)
        main.pack(side="right",fill="both",expand=True)

        self.menu("Business Profile")
        self.top(
            main,
            "Business Profile",
            "Manage your business information"
        )

        box=ctk.CTkFrame(main,fg_color=CARD)
        box.pack(fill="x",padx=60,pady=30)

        fields=[]

        for key,text in [
            ("name","Business Name"),
            ("type","Business Type"),
            ("phone","Phone Number"),
            ("address","Business Address"),
            ("years","Years In Operation")
        ]:
            ctk.CTkLabel(
                box,text=text,
                text_color="#94a3b8"
            ).pack(anchor="w",padx=25,pady=(15,3))

            if key=="address":
                e=ctk.CTkTextbox(box,height=80)
                e.pack(fill="x",padx=25,pady=5)
                e.insert("1.0",self.business[key] or "")
            else:
                e=ctk.CTkEntry(box,height=40)
                e.pack(fill="x",padx=25,pady=5)
                e.insert(0,str(self.business[key] or ""))

            fields.append((key,e))

        ctk.CTkLabel(
            box,text="Currency",
            text_color="#94a3b8"
        ).pack(anchor="w",padx=25,pady=(15,3))

        currency=ctk.CTkComboBox(
            box,
            values=["INR","USD","AED","EUR","GBP"],
            height=40
        )
        currency.set(self.business["currency"])
        currency.pack(fill="x",padx=25,pady=5)

        def save():
            values={}

            for key,e in fields:
                if key=="address":
                    values[key]=e.get("1.0","end").strip()
                else:
                    values[key]=e.get().strip()

            try:
                values["years"]=int(values["years"] or 0)

                db=self.db()
                c=db.cursor()

                c.execute(
                    """
                    UPDATE businesses
                    SET name=%s,type=%s,phone=%s,
                    address=%s,years=%s,currency=%s
                    WHERE user_id=%s
                    """,
                    (
                        values["name"],
                        values["type"],
                        values["phone"],
                        values["address"],
                        values["years"],
                        currency.get(),
                        self.user["id"]
                    )
                )

                db.commit()
                c.close()
                db.close()

                self.business=self.get_business()

                messagebox.showinfo(
                    "Profile",
                    "Business profile updated"
                )

            except:
                messagebox.showerror(
                    "Profile",
                    "Could not update profile"
                )

        ctk.CTkButton(
            box,text="Save Changes",
            height=42,
            command=save
        ).pack(fill="x",padx=25,pady=25)

    def table_style(self):
        style=ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#151c25",
            foreground="white",
            fieldbackground="#151c25",
            rowheight=35,
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background="#1b2430",
            foreground="#94a3b8",
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[("selected","#2563eb")]
        )

    def logout(self):
        self.user=None
        self.business=None
        self.login()

root=ctk.CTk()
App(root)
root.mainloop()
