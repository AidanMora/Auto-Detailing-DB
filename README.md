# 🚗 Auto Detailing DB

A full-featured **Auto Detailing Management System** built with **Python (Tkinter/CustomTkinter)** and **MySQL**.  
The system allows easy management of **customers, vehicles, appointments, and payments**, with integrated **reports, dashboards, and admin tools**.  

This project was created as part of a **Database Systems Final Project**.

---

## ✨ Features

### 🔹 Customer Management
- Add, update, and delete customers  
- Store details: first/last name, email, phone, join date  
- View all customers in a searchable table  

### 🔹 Vehicle Management
- Register and manage customer vehicles  
- Track make, model, license plate  
- Link vehicles directly to customers  

### 🔹 Appointments
- Schedule appointments with customers and vehicles  
- Manage appointment date, start/end time, and status  
- Update status (e.g., *scheduled, completed, canceled*)  
- Delete appointments as needed  

### 🔹 Payments
- Record payments linked to appointments  
- Store payment date, amount, and method  
- View complete payment history  

### 🔹 Reports & Dashboard
- Generate **Recent Payments Summary** (via stored procedure)  
- Monthly appointment chart (Matplotlib)  
- Quick overview of business trends  

### 🔹 Settings
- **Dark Mode toggle** for UI  
- **Wipe All Data** option to clear records (tables remain intact)  

---

## 🗄️ Database Design

The backend is powered by **MySQL**, designed in **3rd Normal Form (3NF)**.  
Core tables include:

- **Customers** → customer details  
- **Vehicles** → linked to customers  
- **Appointments** → links customers & vehicles, tracks scheduling  
- **Payments** → linked to appointments  

Advanced features implemented:
- ✅ Stored Procedures  
- ✅ Views  
- ✅ Triggers  

---

## 🛠️ Tech Stack

- **Frontend:** Python, Tkinter, CustomTkinter, PIL, Matplotlib  
- **Backend:** MySQL (via `mysql-connector-python`)  
- **Tools:** MySQL Workbench, VS Code  

---

## ⚙️ Setup Instructions

1. **Clone the repo**  
   ```bash
   git clone https://github.com/YOUR-USERNAME/Auto-Detailing-DB.git
   cd Auto-Detailing-DB
