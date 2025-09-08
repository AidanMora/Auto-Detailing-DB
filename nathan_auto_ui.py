import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from PIL import Image, ImageTk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from dashboard import DashboardFrame

# Global variables
current_page = {"name": None}
current_page_loader = None
TREEVIEW_STYLE = "Dark.Treeview"
page_refreshers = {}
current_dashboard = None  # Track the current dashboard instance

# --- Custom LabelFrame that gets colors automatically ---
def create_label_frame(parent, text):
    lf = tk.LabelFrame(parent, text=text)
    set_theme(lf)
    return lf, lf

# --- Database config ---
DB_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'nathan_auto_detail'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def verify_login(username, password):
    return username == 'user' and password == 'pass'

def safe_destroy_dashboard():
    """Safely destroy the current dashboard instance."""
    global current_dashboard
    if current_dashboard is not None:
        try:
            print("Attempting safe dashboard cleanup...")
            # First unpack it
            current_dashboard.pack_forget()
            # Give it a moment
            current_dashboard.update_idletasks()
            # Then destroy
            current_dashboard.destroy()
            print("Dashboard safely destroyed")
        except Exception as e:
            print(f"Dashboard cleanup error (will continue): {e}")
        finally:
            current_dashboard = None

def add_simple_dashboard_content(content_frame):
    """Add simple placeholder content for dashboard."""
    info_frame = tk.Frame(content_frame, bg="#2a2a2a", relief="ridge", bd=2)
    info_frame.pack(pady=20, padx=20, fill="x")
    
    tk.Label(info_frame, text="Quick Stats (Placeholder)", 
             fg="white", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(info_frame, text="• Total Customers: Click 'Customers' to view\n• Active Appointments: Click 'Appointments' to view\n• Recent Payments: Click 'Payments' to view", 
             fg="lightgray", bg="#2a2a2a", font=("Arial", 10), justify="left").pack(pady=10)

def clear_frame(frame):
    """Safely clear all widgets from a frame, handling CustomTkinter widgets."""
    # Use the safe dashboard cleanup function
    safe_destroy_dashboard()
    
    # Then clear all remaining widgets
    children = list(frame.winfo_children())  # Create a copy of the list
    
    for widget in children:
        try:
            # Try to unpack/ungrid the widget first
            widget.pack_forget()
            widget.grid_forget()
            widget.place_forget()
        except:
            pass
            
        try:
            # Then try to destroy it
            widget.destroy()
        except Exception as e:
            print(f"Warning: Could not destroy widget {widget.__class__.__name__}: {e}")
            pass

# --- Apply dark theme to ALL tk widgets ---
def set_theme(widget):
    # Dark theme colors
    bg = "#1e1e1e"
    fg = "#ffffff"
    entry_bg = "#2a2a2a"
    disabled_fg = "#9a9a9a"
    highlight = "#3a3a3a"

    # Only style plain tkinter widgets directly
    try:
        import customtkinter as ctk
        CTKBase = (ctk.CTkBaseClass,) if hasattr(ctk, "CTkBaseClass") else tuple()
    except Exception:
        CTKBase = tuple()

    import tkinter as tk
    from tkinter import ttk

    # Apply to plain tk widgets
    if not isinstance(widget, (ttk.Widget,) + CTKBase):
        if isinstance(widget, (tk.Frame, tk.LabelFrame)):
            try:
                widget.configure(bg=bg)
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Label):
            try:
                widget.configure(bg=bg, fg=fg)
            except tk.TclError:
                pass
        elif isinstance(widget, (tk.Entry, tk.Text)):
            try:
                widget.configure(
                    bg=entry_bg,
                    fg=fg,
                    insertbackground=fg,
                    selectbackground=highlight,
                    selectforeground=fg,
                    disabledforeground=disabled_fg,
                    highlightbackground=highlight,
                    highlightcolor=highlight,
                    relief="flat", borderwidth=1
                )
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Button):
            try:
                widget.configure(
                    bg=highlight,  # Use a slightly lighter bg for buttons to make them visible
                    fg=fg, 
                    activebackground=bg, 
                    activeforeground=fg,
                    relief="flat",
                    borderwidth=1
                )
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Checkbutton):
            try:
                widget.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg, selectcolor=bg)
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Radiobutton):
            try:
                widget.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg, selectcolor=bg)
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Listbox):
            try:
                widget.configure(bg=entry_bg, fg=fg, selectbackground=highlight, selectforeground=fg)
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Scale):
            try:
                widget.configure(bg=bg, fg=fg, highlightbackground=bg)
            except tk.TclError:
                pass
        elif isinstance(widget, tk.Spinbox):
            try:
                widget.configure(bg=entry_bg, fg=fg, disabledforeground=disabled_fg)
            except tk.TclError:
                pass

    # Recurse into all children
    for child in widget.winfo_children():
        set_theme(child)

# --- Apply dark theme defaults for NEW tk widgets ---
def apply_defaults_to(root):
    bg, fg, entry_bg, active_bg = "#1e1e1e", "#ffffff", "#2a2a2a", "#444444"

    root.option_add("*Background", bg)
    root.option_add("*foreground", fg)
    root.option_add("*Frame.background", bg)
    root.option_add("*Label.background", bg)
    root.option_add("*Label.foreground", fg)
    root.option_add("*Entry.background", entry_bg)
    root.option_add("*Entry.foreground", fg)
    root.option_add("*Entry.insertBackground", fg)
    root.option_add("*Button.background", active_bg)
    root.option_add("*Button.foreground", fg)
    root.option_add("*Button.activeBackground", "#555555")
    root.option_add("*Button.activeforeground", fg)
    root.option_add("*Button.relief", "flat")

# ---------- CUSTOMERS ----------
def load_customers(parent):
    clear_frame(parent)
    tk.Label(parent, text="Customer Management", font=('Arial', 16)).pack()

    input_container = tk.Frame(parent)
    input_container.pack(pady=10, fill='x')

    add_frame_container, add_frame = create_label_frame(input_container, "Add Customer")
    add_frame_container.pack(side='left', padx=10, fill='both', expand=True)

    tk.Label(add_frame, text="First Name").grid(row=0, column=0)
    fn_e = tk.Entry(add_frame, width=30); fn_e.grid(row=0, column=1)

    tk.Label(add_frame, text="Last Name").grid(row=1, column=0)
    ln_e = tk.Entry(add_frame, width=30); ln_e.grid(row=1, column=1)

    tk.Label(add_frame, text="Email").grid(row=2, column=0)
    em_e = tk.Entry(add_frame, width=30); em_e.grid(row=2, column=1)

    tk.Label(add_frame, text="Phone").grid(row=3, column=0)
    ph_e = tk.Entry(add_frame, width=30); ph_e.grid(row=3, column=1)

    def add():
        fn, ln, em, ph = fn_e.get(), ln_e.get(), em_e.get(), ph_e.get()
        if not all([fn, ln, em, ph]):
            return messagebox.showerror("Error", "All fields required.")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""INSERT INTO Customers
                (FirstName, LastName, Email, Phone, JoinDate)
                VALUES (%s,%s,%s,%s,CURDATE())""", (fn, ln, em, ph))
            conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Insert Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (fn_e, ln_e, em_e, ph_e): e.delete(0, tk.END)

    tk.Button(add_frame, text="Add Customer", command=add).grid(row=4, column=0, columnspan=2, pady=10)

    update_frame_container, update_frame = create_label_frame(input_container, "Update Customer")
    update_frame_container.pack(side='left', padx=10, fill='both', expand=True)

    tk.Label(update_frame, text="Customer ID").grid(row=0, column=0)
    cid_update = tk.Entry(update_frame, width=10); cid_update.grid(row=0, column=1)

    tk.Label(update_frame, text="First Name").grid(row=0, column=2)
    fn_update = tk.Entry(update_frame, width=20); fn_update.grid(row=0, column=3)

    tk.Label(update_frame, text="Last Name").grid(row=1, column=0)
    ln_update = tk.Entry(update_frame, width=20); ln_update.grid(row=1, column=1)

    tk.Label(update_frame, text="Email").grid(row=1, column=2)
    em_update = tk.Entry(update_frame, width=20); em_update.grid(row=1, column=3)

    tk.Label(update_frame, text="Phone").grid(row=2, column=0)
    ph_update = tk.Entry(update_frame, width=20); ph_update.grid(row=2, column=1)

    def update_customer():
        cid = cid_update.get()
        if not cid: return messagebox.showerror("Error", "Customer ID is required.")
        fields, values = [], []
        if fn_update.get(): fields.append("FirstName=%s"); values.append(fn_update.get())
        if ln_update.get(): fields.append("LastName=%s");  values.append(ln_update.get())
        if em_update.get(): fields.append("Email=%s");     values.append(em_update.get())
        if ph_update.get(): fields.append("Phone=%s");     values.append(ph_update.get())
        if not fields: return messagebox.showwarning("No Update", "No fields to update.")
        q = f"UPDATE Customers SET {', '.join(fields)} WHERE CustomerID=%s"; values.append(cid)
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(q, tuple(values)); conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Update Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (cid_update, fn_update, ln_update, em_update, ph_update): e.delete(0, tk.END)

    tk.Button(update_frame, text="Update Customer", command=update_customer).grid(row=3, column=0, columnspan=4, pady=10)

    tree_frame = tk.Frame(parent); tree_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(tree_frame, columns=("ID", "First", "Last", "Email", "Phone"), show='headings')
    tree.configure(style=TREEVIEW_STYLE)
    for col in tree["columns"]: tree.heading(col, text=col)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    def delete_customer():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Delete", "No row selected.")
        cid = tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete customer ID {cid}?"):
            try:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM Customers WHERE CustomerID=%s", (cid,))
                conn.commit()
            except mysql.connector.Error as err:
                messagebox.showerror("Delete Error", str(err))
            finally:
                try: cur.close(); conn.close()
                except: pass
            load()

    tk.Button(parent, text="Delete Selected", command=delete_customer).pack(pady=5)

    def load():
        tree.delete(*tree.get_children())
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT CustomerID, FirstName, LastName, Email, Phone FROM Customers")
            for row in cur.fetchall(): tree.insert('', 'end', values=row)
            cur.close(); conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    load()

# ---------- VEHICLES ----------
def load_vehicles(parent):
    clear_frame(parent)
    tk.Label(parent, text="Vehicle Management", font=('Arial', 16)).pack()

    input_container = tk.Frame(parent); input_container.pack(pady=10, fill='x')

    add_frame_container, add_frame = create_label_frame(input_container, "Add Vehicle")
    add_frame_container.pack(side='left', padx=10, fill='both', expand=True)

    update_frame_container, update_frame = create_label_frame(input_container, "Update Vehicle Info")
    update_frame_container.pack(side='left', padx=10, fill='both', expand=True)

    tree_frame = tk.Frame(parent); tree_frame.pack(fill='both', expand=True)

    def load():
        tree.delete(*tree.get_children())
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT v.VehicleID, c.FirstName, c.LastName, v.Make, v.Model, v.LicensePlate
                FROM Vehicles v
                JOIN Customers c ON v.CustomerID = c.CustomerID
            """)
            for row in cur.fetchall(): tree.insert('', 'end', values=row)
            cur.close(); conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def add():
        cid, make, model, plate = cid_e.get(), mk_e.get(), md_e.get(), lp_e.get()
        if not all([cid, make, model, plate]):
            return messagebox.showerror("Error", "All fields required.")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""INSERT INTO Vehicles (CustomerID, Make, Model, LicensePlate)
                           VALUES (%s,%s,%s,%s)""", (cid, make, model, plate))
            conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Insert Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (cid_e, mk_e, md_e, lp_e): e.delete(0, tk.END)

    def delete_vehicle():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Delete", "No row selected.")
        vid = tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete vehicle ID {vid}?"):
            try:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM Vehicles WHERE VehicleID=%s", (vid,))
                conn.commit()
            except mysql.connector.Error as err:
                messagebox.showerror("Delete Error", str(err))
            finally:
                try: cur.close(); conn.close()
                except: pass
            load()

    def update_vehicle():
        vid = vid_update.get()
        if not vid: return messagebox.showerror("Error", "Vehicle ID is required.")
        fields, values = [], []
        if make_update.get():  fields.append("Make=%s");  values.append(make_update.get())
        if model_update.get(): fields.append("Model=%s"); values.append(model_update.get())
        if plate_update.get(): fields.append("LicensePlate=%s"); values.append(plate_update.get())
        if not fields: return messagebox.showwarning("No Update", "No fields to update.")
        q = f"UPDATE Vehicles SET {', '.join(fields)} WHERE VehicleID=%s"; values.append(vid)
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(q, tuple(values)); conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Update Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (vid_update, make_update, model_update, plate_update): e.delete(0, tk.END)

    tk.Label(add_frame, text="Customer ID").grid(row=0, column=0)
    cid_e = tk.Entry(add_frame, width=30); cid_e.grid(row=0, column=1)

    tk.Label(add_frame, text="Make").grid(row=1, column=0)
    mk_e = tk.Entry(add_frame, width=30); mk_e.grid(row=1, column=1)

    tk.Label(add_frame, text="Model").grid(row=2, column=0)
    md_e = tk.Entry(add_frame, width=30); md_e.grid(row=2, column=1)

    tk.Label(add_frame, text="License Plate").grid(row=3, column=0)
    lp_e = tk.Entry(add_frame, width=30); lp_e.grid(row=3, column=1)

    tk.Button(add_frame, text="Add Vehicle", command=add).grid(row=4, column=0, columnspan=2, pady=10)

    tk.Label(update_frame, text="Vehicle ID").grid(row=0, column=0)
    vid_update = tk.Entry(update_frame, width=10); vid_update.grid(row=0, column=1)

    tk.Label(update_frame, text="Make").grid(row=1, column=0)
    make_update = tk.Entry(update_frame, width=30); make_update.grid(row=1, column=1)

    tk.Label(update_frame, text="Model").grid(row=2, column=0)
    model_update = tk.Entry(update_frame, width=30); model_update.grid(row=2, column=1)

    tk.Label(update_frame, text="License Plate").grid(row=3, column=0)
    plate_update = tk.Entry(update_frame, width=30); plate_update.grid(row=3, column=1)

    tk.Button(update_frame, text="Update Vehicle", command=update_vehicle).grid(row=4, column=0, columnspan=2, pady=10)

    tree = ttk.Treeview(tree_frame, columns=("ID", "First", "Last", "Make", "Model", "Plate"), show='headings')
    tree.configure(style=TREEVIEW_STYLE)
    for col in tree["columns"]: tree.heading(col, text=col)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    tk.Button(parent, text="Delete Selected", command=delete_vehicle).pack(pady=5)

    load()

# ---------- APPOINTMENTS ----------
def load_appointments(parent):
    clear_frame(parent)
    tk.Label(parent, text="Appointments Management", font=('Arial', 16)).pack()

    container_frame = tk.Frame(parent); container_frame.pack(pady=10, fill='x')

    add_frame_container, add_frame = create_label_frame(container_frame, "Add Appointment")
    add_frame_container.pack(side='left', padx=10, fill='both', expand=True)

    update_frame_container, update_frame = create_label_frame(container_frame, "Update Appointment Status")
    update_frame_container.pack(side='left', padx=10, fill='both', expand=True)

    tk.Label(add_frame, text="Customer ID").grid(row=0, column=0, padx=5, pady=5)
    cust_id_e = tk.Entry(add_frame, width=30); cust_id_e.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Vehicle ID").grid(row=1, column=0, padx=5, pady=5)
    veh_id_e  = tk.Entry(add_frame, width=30); veh_id_e.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Date (YYYY-MM-DD)").grid(row=2, column=0, padx=5, pady=5)
    date_e = tk.Entry(add_frame, width=30); date_e.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Start Time (HH:MM:SS)").grid(row=3, column=0, padx=5, pady=5)
    start_e = tk.Entry(add_frame, width=30); start_e.grid(row=3, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="End Time (HH:MM:SS)").grid(row=4, column=0, padx=5, pady=5)
    end_e = tk.Entry(add_frame, width=30); end_e.grid(row=4, column=1, padx=5, pady=5)

    tk.Button(add_frame, text="Add Appointment", command=lambda: add_appointment()).grid(row=5, column=0, columnspan=2, pady=10)

    tk.Label(update_frame, text="Appointment ID").grid(row=0, column=0, padx=5, pady=5)
    appt_id_e = tk.Entry(update_frame, width=30); appt_id_e.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(update_frame, text="New Status").grid(row=1, column=0, padx=5, pady=5)
    status_e = tk.Entry(update_frame, width=30); status_e.grid(row=1, column=1, padx=5, pady=5)

    tk.Button(update_frame, text="Update Status", command=lambda: update_status()).grid(row=2, column=0, columnspan=2, pady=10)

    tree_frame = tk.Frame(parent); tree_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(tree_frame, columns=("ID", "Customer", "Vehicle", "Date", "Start", "End", "Status"), show='headings')
    tree.configure(style=TREEVIEW_STYLE)
    for col in tree["columns"]: tree.heading(col, text=col)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    def load():
        tree.delete(*tree.get_children())
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT a.AppointmentID, c.FirstName, v.Make, a.AppointmentDate, a.StartTime, a.EndTime, a.Status
                FROM Appointments a
                JOIN Customers c ON a.CustomerID = c.CustomerID
                JOIN Vehicles v ON a.VehicleID = v.VehicleID
            """)
            for row in cur.fetchall(): tree.insert('', 'end', values=row)
            cur.close(); conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def add_appointment():
        cid, vid, date, start, end = cust_id_e.get(), veh_id_e.get(), date_e.get(), start_e.get(), end_e.get()
        if not all([cid, vid, date, start, end]):
            return messagebox.showerror("Error", "All fields are required.")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                INSERT INTO Appointments (CustomerID, VehicleID, AppointmentDate, StartTime, EndTime, Status)
                VALUES (%s,%s,%s,%s,%s,'scheduled')
            """, (cid, vid, date, start, end))
            conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Insert Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (cust_id_e, veh_id_e, date_e, start_e, end_e): e.delete(0, tk.END)

    def update_status():
        aid, new_status = appt_id_e.get(), status_e.get()
        if not aid or not new_status:
            return messagebox.showerror("Error", "Both fields required.")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("UPDATE Appointments SET Status=%s WHERE AppointmentID=%s", (new_status, aid))
            conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Update Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (appt_id_e, status_e): e.delete(0, tk.END)

    def delete_appointment():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Delete", "No row selected.")
        appt_id = tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete appointment ID {appt_id}?"):
            try:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM Appointments WHERE AppointmentID=%s", (appt_id,))
                conn.commit()
            except mysql.connector.Error as err:
                messagebox.showerror("Delete Error", str(err))
            finally:
                try: cur.close(); conn.close()
                except: pass
            load()

    tk.Button(parent, text="Delete Selected", command=delete_appointment).pack(pady=5)

    load()

# ---------- PAYMENTS ----------
def load_payments(parent):
    clear_frame(parent)
    tk.Label(parent, text="Payments Management", font=('Arial', 16)).pack()

    input_frame = tk.Frame(parent)
    input_frame.pack(pady=10)

    tk.Label(input_frame, text="Appointment ID").grid(row=0, column=0)
    appt_id_e = tk.Entry(input_frame, width=50); appt_id_e.grid(row=0, column=1)

    tk.Label(input_frame, text="Date").grid(row=1, column=0)
    date_e = tk.Entry(input_frame, width=50); date_e.grid(row=1, column=1)

    tk.Label(input_frame, text="Amount").grid(row=2, column=0)
    amount_e = tk.Entry(input_frame, width=50); amount_e.grid(row=2, column=1)

    tk.Label(input_frame, text="Method").grid(row=3, column=0)
    method_e = tk.Entry(input_frame, width=50); method_e.grid(row=3, column=1)

    def load():
        tree.delete(*tree.get_children())
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT PaymentID, AppointmentID, PaymentDate, Amount, PaymentMethod FROM Payments")
            for row in cur.fetchall(): tree.insert('', 'end', values=row)
            cur.close(); conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def add_payment():
        appt_id, date, amount, method = appt_id_e.get(), date_e.get(), amount_e.get(), method_e.get()
        if not all([appt_id, date, amount, method]):
            return messagebox.showerror("Error", "All fields are required.")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""INSERT INTO Payments (AppointmentID, PaymentDate, Amount, PaymentMethod)
                           VALUES (%s,%s,%s,%s)""", (appt_id, date, amount, method))
            conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Insert Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass
        load()
        for e in (appt_id_e, date_e, amount_e, method_e): e.delete(0, tk.END)

    def delete_payment():
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Delete", "No row selected.")
        pid = tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete payment ID {pid}?"):
            try:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM Payments WHERE PaymentID=%s", (pid,))
                conn.commit()
            except mysql.connector.Error as err:
                messagebox.showerror("Delete Error", str(err))
            finally:
                try: cur.close(); conn.close()
                except: pass
            load()

    tk.Button(input_frame, text="Add Payment", command=add_payment).grid(row=4, column=0, columnspan=2, pady=10)

    tree_frame = tk.Frame(parent); tree_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(tree_frame, columns=("ID", "Appointment ID", "Date", "Amount", "Method"), show='headings')
    tree.configure(style=TREEVIEW_STYLE)
    for col in tree["columns"]: tree.heading(col, text=col)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    tk.Button(parent, text="Delete Selected", command=delete_payment).pack(pady=5)

    load()

# ---------- SETTINGS ----------
def load_settings(parent):
    clear_frame(parent)
    tk.Label(parent, text="Settings", font=('Arial', 16)).pack(pady=10)

    desc = ("⚠️ Wipe ALL Data\n\n"
            "This will delete all rows from your database tables.\n"
            "Use only if you are sure. This action cannot be undone.")
    tk.Label(parent, text=desc, justify="left").pack(pady=5)

    def clear_all_data():
        if not messagebox.askyesno("Really wipe ALL data?", "This will remove ALL rows. Continue?"):
            return
        if not messagebox.askyesno("Are you absolutely sure?", "This cannot be undone. Proceed?"):
            return
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            tables_in_order = [
                "AppointmentAddOns","AppointmentServices","Reviews","Payments",
                "Appointments","Vehicles","Services","ServiceAddOns","Customers"
            ]
            for tbl in tables_in_order:
                try: cur.execute(f"TRUNCATE TABLE {tbl}")
                except mysql.connector.Error as e: print(f"Skipping {tbl}: {e}")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            conn.commit()
            messagebox.showinfo("Done", "All data has been wiped.")
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed wiping  {err}")
        finally:
            try: cur.close(); conn.close()
            except: pass

    tk.Button(parent, text="Wipe ALL Data", command=clear_all_data,
              bg="#b00020", fg="#ffffff", padx=10, pady=6).pack(pady=15)

# ---------- REPORTS ----------
def load_reports(parent):
    clear_frame(parent)
    tk.Label(parent, text="Reports / Views", font=('Arial', 16)).pack()

    tk.Label(parent, text="Enter # of days for recent payments summary:").pack()
    days_entry = tk.Entry(parent); days_entry.pack()

    tree = ttk.Treeview(parent, columns=("PaymentID", "AppointmentID", "Amount", "Date"), show='headings')
    tree.configure(style=TREEVIEW_STYLE)
    for col in tree["columns"]: tree.heading(col, text=col)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    def run_summary():
        tree.delete(*tree.get_children())
        try:
            days = int(days_entry.get())
        except ValueError:
            return messagebox.showerror("Error", "Please enter a whole number of days.")
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.callproc("SummarizeRecentPayments", [days])
            for result in cur.stored_results():
                for row in result.fetchall():
                    tree.insert('', 'end', values=row)
        except mysql.connector.Error as err:
            messagebox.showerror("DB Error", str(err))
        finally:
            try: cur.close(); conn.close()
            except: pass

    tk.Button(parent, text="Run Report", command=run_summary).pack(pady=10)

# ---------- LOGIN & MAIN UI ----------
def open_main_ui():
    login.destroy()
    global root, sidebar, content_frame

    root = tk.Tk()
    try:
        root.iconbitmap("NADLOGO.ico")
    except tk.TclError:
        pass
    root.title("Nathan Auto Detail - Dashboard")
    root.geometry("1000x600")

    # Apply dark theme defaults
    apply_defaults_to(root)

    # Set CTk to dark mode
    ctk.set_appearance_mode("dark")
    
    # Setup ttk styles
    style = ttk.Style()
    style.theme_use("clam")
    
    # Colors
    APP_BG = "#1e1e1e"
    FG = "#ffffff"
    ENTRY_BG = "#2a2a2a"
    HOVER_BG = "#555555"
    ACTIVE_BG = "#444444"
    BORDER = "#3a3a3a"
    
    # Configure basic styles
    style.configure(".", background=APP_BG, foreground=FG)
    style.map(".", background=[("!disabled", APP_BG)], foreground=[("!disabled", FG)])
    
    style.configure("TFrame", background=APP_BG)
    style.configure("TLabel", background=APP_BG, foreground=FG)
    style.configure("TLabelframe", background=APP_BG, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=APP_BG, foreground=FG)
    
    # Entry style
    style.configure(
        "Theme.TEntry",
        fieldbackground=ENTRY_BG,
        background=ENTRY_BG,
        foreground=FG,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=3
    )
    style.map(
        "Theme.TEntry",
        fieldbackground=[("readonly", ENTRY_BG), ("focus", ENTRY_BG)],
        foreground=[("disabled", FG), ("!disabled", FG)]
    )
    
    # Button styles
    style.configure("TButton", background=ACTIVE_BG, foreground=FG, bordercolor=BORDER, relief="flat", padding=(8, 4))
    style.map("TButton", background=[("active", HOVER_BG), ("!active", ACTIVE_BG)], foreground=[("!disabled", FG)])
    
    style.configure("Nav.TButton", background=ACTIVE_BG, foreground=FG, bordercolor=BORDER, relief="flat", padding=(10, 6))
    style.map("Nav.TButton", background=[("pressed", HOVER_BG), ("active", HOVER_BG), ("!active", ACTIVE_BG)],
                             foreground=[("!disabled", FG)])
    
    # Treeview
    global TREEVIEW_STYLE
    tv_style = "Dark.Treeview"
    style.configure(tv_style, background=APP_BG, fieldbackground=APP_BG, foreground=FG, bordercolor=BORDER, rowheight=25)
    style.map(tv_style, background=[("selected", HOVER_BG), ("!selected", APP_BG)], foreground=[("selected", FG), ("!selected", FG)])
    style.layout(tv_style, [("Treeview.treearea", {"sticky": "nswe"})])
    style.configure("Treeview.Heading", background=ACTIVE_BG, foreground=FG, relief="flat", bordercolor=BORDER)
    style.map("Treeview.Heading", background=[("active", HOVER_BG), ("!active", ACTIVE_BG)], foreground=[("!disabled", FG)])
    
    TREEVIEW_STYLE = tv_style

    # Create main layout
    sidebar = tk.Frame(root)
    sidebar.pack(side='left', fill='y')

    content_frame = tk.Frame(root)
    content_frame.pack(side='right', expand=True, fill='both', padx=(20, 0))  # Add 20px left padding
    
    # Configure root, sidebar and content frame colors
    try:
        root.configure(bg=APP_BG)
        sidebar.configure(bg=APP_BG, highlightbackground=APP_BG, highlightcolor=APP_BG)
        content_frame.configure(bg=APP_BG, highlightbackground=APP_BG, highlightcolor=APP_BG)
    except Exception:
        pass
    
    # Apply theme to existing widgets
    set_theme(root)

    def show_dashboard():
        global current_page_loader, current_dashboard
        current_page_loader = show_dashboard
        current_page["name"] = "dashboard"
        print("show_dashboard called")  # Debug print

        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Add header
            tk.Label(content_frame, text="Dashboard", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            
            # Create a dedicated container for the dashboard
            dashboard_container = tk.Frame(content_frame, bg="#1e1e1e")
            dashboard_container.pack(fill="both", expand=True, pady=10)
            
            # Try to load the actual dashboard
            try:
                print("Attempting to load dashboard...")
                
                # Make sure any existing dashboard is cleaned up first
                safe_destroy_dashboard()
                
                # Test database connection first
                try:
                    test_conn = get_connection()
                    test_conn.close()
                    print("Database connection successful")
                except Exception as db_e:
                    raise Exception(f"Database connection failed: {db_e}")
                
                dash = DashboardFrame(
                    dashboard_container,  # Use the dedicated container instead of content_frame
                    get_connection=get_connection,
                    get_is_dark=lambda: True  # Always return True since we're always in dark mode
                )
                
                # Store reference to dashboard instance
                global current_dashboard
                current_dashboard = dash
                
                dash.pack(fill="both", expand=True, pady=10)
                print("Dashboard loaded successfully")
                
            except ImportError as import_e:
                print(f"Dashboard import error: {import_e}")
                tk.Label(content_frame, text="📊 Dashboard module not found - using simple view", 
                         fg="yellow", bg="#1e1e1e", font=("Arial", 12)).pack(pady=10)
                # Add simple placeholder content
                add_simple_dashboard_content(dashboard_container)
                
            except Exception as dash_e:
                print(f"Dashboard error: {dash_e}")
                tk.Label(content_frame, text="📊 Dashboard temporarily unavailable", 
                         fg="orange", bg="#1e1e1e", font=("Arial", 12)).pack(pady=10)
                tk.Label(content_frame, text=f"Error: {dash_e}", 
                         fg="red", bg="#1e1e1e", font=("Arial", 10)).pack(pady=5)
                # Add simple placeholder content
                add_simple_dashboard_content(dashboard_container)
                
        except Exception as e:
            print(f"Error in show_dashboard: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Dashboard Error: {e}", 
                    fg="red", bg="#1e1e1e", font=("Arial", 16)).pack(expand=True)

    def show_customers():
        global current_page_loader
        current_page_loader = show_customers
        current_page["name"] = "customers"
        print("show_customers called")  # Debug print
        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Simple test content first
            tk.Label(content_frame, text="Customers", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            tk.Label(content_frame, text="Customer Management Page", 
                    fg="white", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)
            
            # Try to load the actual customers content
            try:
                load_customers(content_frame)
                set_theme(content_frame)
            except Exception as load_e:
                print(f"Error in load_customers: {load_e}")
                tk.Label(content_frame, text="Customer functionality temporarily unavailable", 
                         fg="orange", bg="#1e1e1e").pack(pady=10)
                
        except Exception as e:
            print(f"Error in show_customers: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Customers Error: {e}", 
                    fg="red", bg="#1e1e1e").pack()

    def show_vehicles():
        global current_page_loader
        current_page_loader = show_vehicles
        current_page["name"] = "vehicles"
        print("show_vehicles called")  # Debug print
        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Simple test content
            tk.Label(content_frame, text="Vehicles", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            tk.Label(content_frame, text="Vehicle Management Page", 
                    fg="white", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)
                    
            try:
                load_vehicles(content_frame)
                set_theme(content_frame)
            except Exception as load_e:
                print(f"Error in load_vehicles: {load_e}")
                tk.Label(content_frame, text="Vehicle functionality temporarily unavailable", 
                         fg="orange", bg="#1e1e1e").pack(pady=10)
                         
        except Exception as e:
            print(f"Error in show_vehicles: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Vehicles Error: {e}", fg="red", bg="#1e1e1e").pack()

    def show_appointments():
        global current_page_loader
        current_page_loader = show_appointments
        current_page["name"] = "appointments"
        print("show_appointments called")  # Debug print
        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Simple test content first
            tk.Label(content_frame, text="Appointments", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            tk.Label(content_frame, text="Appointment Management Page", 
                    fg="white", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)
                    
            try:
                load_appointments(content_frame)
                set_theme(content_frame)
            except Exception as load_e:
                print(f"Error in load_appointments: {load_e}")
                tk.Label(content_frame, text="Appointment functionality temporarily unavailable", 
                         fg="orange", bg="#1e1e1e").pack(pady=10)
                         
        except Exception as e:
            print(f"Error in show_appointments: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Appointments Error: {e}", fg="red", bg="#1e1e1e").pack()

    def show_payments():
        global current_page_loader
        current_page_loader = show_payments
        current_page["name"] = "payments"
        print("show_payments called")  # Debug print
        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Simple test content first
            tk.Label(content_frame, text="Payments", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            tk.Label(content_frame, text="Payment Management Page", 
                    fg="white", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)
                    
            try:
                load_payments(content_frame)
                set_theme(content_frame)
            except Exception as load_e:
                print(f"Error in load_payments: {load_e}")
                tk.Label(content_frame, text="Payment functionality temporarily unavailable", 
                         fg="orange", bg="#1e1e1e").pack(pady=10)
                         
        except Exception as e:
            print(f"Error in show_payments: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Payments Error: {e}", fg="red", bg="#1e1e1e").pack()

    def show_reports():
        global current_page_loader
        current_page_loader = show_reports
        current_page["name"] = "reports"
        print("show_reports called")  # Debug print
        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Simple test content first
            tk.Label(content_frame, text="Reports", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            tk.Label(content_frame, text="Reports and Analytics Page", 
                    fg="white", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)
                    
            try:
                load_reports(content_frame)
                set_theme(content_frame)
            except Exception as load_e:
                print(f"Error in load_reports: {load_e}")
                tk.Label(content_frame, text="Reports functionality temporarily unavailable", 
                         fg="orange", bg="#1e1e1e").pack(pady=10)
                         
        except Exception as e:
            print(f"Error in show_reports: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Reports Error: {e}", fg="red", bg="#1e1e1e").pack()

    def show_settings():
        global current_page_loader
        current_page_loader = show_settings
        current_page["name"] = "settings"
        print("show_settings called")  # Debug print
        try:
            clear_frame(content_frame)
            content_frame.configure(bg="#1e1e1e")
            
            # Simple test content first
            tk.Label(content_frame, text="Settings", fg="white", bg="#1e1e1e", 
                    font=("Arial", 24)).pack(pady=20)
            tk.Label(content_frame, text="Application Settings Page", 
                    fg="white", bg="#1e1e1e", font=("Arial", 14)).pack(pady=10)
                    
            try:
                load_settings(content_frame)
                set_theme(content_frame)
            except Exception as load_e:
                print(f"Error in load_settings: {load_e}")
                tk.Label(content_frame, text="Settings functionality temporarily unavailable", 
                         fg="orange", bg="#1e1e1e").pack(pady=10)
                         
        except Exception as e:
            print(f"Error in show_settings: {e}")
            clear_frame(content_frame)
            tk.Label(content_frame, text=f"Settings Error: {e}", fg="red", bg="#1e1e1e").pack()

    # Define page refreshers
    global page_refreshers
    page_refreshers = {
        "dashboard": show_dashboard,
        "customers": show_customers,
        "vehicles": show_vehicles,
        "appointments": show_appointments,
        "payments": show_payments,
        "reports": show_reports,
        "settings": show_settings,
    }

    # Load logo
    try:
        logo_img = Image.open("NADLOGO.png").resize((100, 100))
        logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(sidebar, image=logo)
        logo_label.image = logo
        logo_label.pack(pady=10)
    except Exception as e:
        print("Logo failed to load:", e)

    # Create navigation buttons - use tk.Button to ensure visibility
    tk.Button(sidebar, text="Dashboard", command=show_dashboard, 
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)
    tk.Button(sidebar, text="Customers", command=show_customers,
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)
    tk.Button(sidebar, text="Vehicles", command=show_vehicles,
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)
    tk.Button(sidebar, text="Appointments", command=show_appointments,
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)
    tk.Button(sidebar, text="Payments", command=show_payments,
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)
    tk.Button(sidebar, text="Reports", command=show_reports,
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)
    tk.Button(sidebar, text="Settings", command=show_settings,
              bg=ACTIVE_BG, fg=FG, activebackground=HOVER_BG, activeforeground=FG,
              relief="flat", borderwidth=1, pady=6, width=25).pack(pady=5)

    # Show dashboard initially
    show_dashboard()
    root.mainloop()

def try_login():
    if verify_login(user_e.get(), pass_e.get()):
        open_main_ui()
    else:
        messagebox.showerror("Login Failed", "Incorrect username or password.")

# Create login window
login = tk.Tk()
try:
    login.iconbitmap("NADLOGO.ico")
except tk.TclError:
    pass
login.title("Login")
login.geometry("300x300")

try:
    logo_img = Image.open("NADLOGO.png").resize((120, 120))
    logo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(login, image=logo)
    logo_label.image = logo
    logo_label.pack(pady=10)
except Exception as e:
    print("Login logo failed to load:", e)

tk.Label(login, text="Username").pack(pady=5)
user_e = tk.Entry(login); user_e.pack()
tk.Label(login, text="Password").pack(pady=5)
pass_e = tk.Entry(login, show="*"); pass_e.pack()
tk.Button(login, text="Login", command=try_login).pack(pady=15)
login.mainloop()