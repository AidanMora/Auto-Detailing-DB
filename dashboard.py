# dashboard.py
import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DARK_BG = "#242424"
DARK_AX = "#1e1e1e"
LIGHT_BG = "#ffffff"
LIGHT_AX = "#ffffff"

class DashboardFrame(ctk.CTkFrame):
    """
    Dashboard:
      • Monthly sales (line)
      • Top 5 services by revenue (bar)
      • Service mix (pie)

    Args:
        parent: tk widget
        get_connection: callable returning a mysql connection
        get_is_dark: callable returning True if dark mode is on
    """
    def __init__(self, parent, get_connection, get_is_dark=lambda: False):
        super().__init__(parent)
        self.get_connection = get_connection
        self.get_is_dark = get_is_dark

        # Controls
        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkLabel(controls, text="Start (YYYY-MM-DD):").pack(side="left", padx=(5, 4))
        self.start_entry = ctk.CTkEntry(controls, width=140); self.start_entry.pack(side="left")

        ctk.CTkLabel(controls, text="End (YYYY-MM-DD):").pack(side="left", padx=(10, 4))
        self.end_entry = ctk.CTkEntry(controls, width=140); self.end_entry.pack(side="left")

        end_default = datetime.today().date()
        start_default = end_default - timedelta(days=90)
        self.start_entry.insert(0, str(start_default))
        self.end_entry.insert(0, str(end_default))

        # Chart selector dropdown
        ctk.CTkLabel(controls, text="Chart:").pack(side="right", padx=(20, 4))
        self.chart_selector = ctk.CTkComboBox(controls, width=140, 
                                            values=["Revenue Trend", "Service Mix"],
                                            command=self.on_chart_change)
        self.chart_selector.pack(side="right", padx=(0, 10))
        self.chart_selector.set("Revenue Trend")  # Default selection

        ctk.CTkButton(controls, text="Refresh", command=self.refresh_all).pack(side="right", padx=8, pady=6)

        # Chart grid - now 2 columns: KPI (wide), Selected Chart
        self.charts_frame = ctk.CTkFrame(self)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # TO CHANGE KPI WIDTH: Adjust the weight values below (INTEGERS ONLY)
        # Higher weight = wider section. Examples:
        # weight=3 makes KPI section 3x wider than chart (3:1 ratio)
        # weight=2 makes KPI section 2x wider than chart (2:1 ratio) 
        # weight=1 makes them equal width (1:1 ratio)
        # Current: Chart section gets more space (3:4 ratio = chart is wider)
        self.charts_frame.grid_columnconfigure(0, weight=3)  # KPI section (smaller)
        self.charts_frame.grid_columnconfigure(1, weight=4)  # Selected chart (larger)
        self.charts_frame.grid_rowconfigure(0, weight=1)
        self.charts_frame.grid_rowconfigure(1, weight=1)

        # Canvas placeholders
        self.canvas_kpi = None
        self.canvas_right_chart = None  # This will hold either revenue trend or service mix

        # Delay initial refresh to ensure widgets are fully initialized
        self.after(100, self.initial_refresh)
    
    def on_chart_change(self, selection):
        """Handle chart selector dropdown change."""
        # Get current date range
        start_s = self.start_entry.get().strip()
        end_s = self.end_entry.get().strip()
        
        try:
            start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
            
            # Clear existing right chart
            if self.canvas_right_chart:
                try:
                    if hasattr(self.canvas_right_chart, 'get_tk_widget'):
                        self.canvas_right_chart.get_tk_widget().destroy()
                    else:
                        self.canvas_right_chart.destroy()
                except:
                    pass
                self.canvas_right_chart = None
            
            # Draw selected chart
            if selection == "Revenue Trend":
                self.draw_revenue_trend_chart(start_date, end_date)
            elif selection == "Service Mix":
                services = self.load_service_revenue(start_date, end_date)
                self.draw_service_mix_pie(services)
                
        except Exception as e:
            print(f"Chart change error: {e}")

    # ---------- DB helper ----------
    def _fetch(self, query, params=None):
        conn = None
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(query, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception as e:
            messagebox.showerror("DB Error", f"{e}")
            return []
        finally:
            if conn:
                conn.close()

    # ---------- Schema helpers ----------
    def _has_col(self, table, column):
        q = """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
        """
        rows = self._fetch(q, (table, column))
        return bool(rows and rows[0][0] > 0)

    def _service_name_col(self):
        for cand in ("Name", "ServiceName", "Title", "Service_Title"):
            if self._has_col("Services", cand):
                return cand
        return None

    # ---------- Data loaders ----------
    def load_monthly_sales(self, start_date, end_date):
        q = """
            SELECT DATE_FORMAT(PaymentDate, '%Y-%m-01') AS month_start,
                   SUM(Amount) AS total_sales
            FROM Payments
            WHERE PaymentDate >= %s AND PaymentDate < DATE_ADD(%s, INTERVAL 1 DAY)
            GROUP BY DATE_FORMAT(PaymentDate, '%Y-%m-01')
            ORDER BY month_start ASC;
        """
        rows = self._fetch(q, (start_date, end_date))
        return [(str(m)[:7], float(t or 0)) for (m, t) in rows]

    def load_service_revenue(self, start_date, end_date):
        """
        Returns [(service_name, revenue_or_count), ...]
        Tries in order:
          1) AppointmentServices.LineTotal
          2) Appointments.TotalPrice with Appointments.ServiceID
          3) Fallback: count of uses in AppointmentServices
        """
        name_col = self._service_name_col()
        if not name_col:
            return [("Unknown", 0.0)]

        has_as = self._has_col("AppointmentServices", "ServiceID")
        has_line_total = self._has_col("AppointmentServices", "ActualPrice")
        has_appt_serviceid = self._has_col("Appointments", "ServiceID")
        has_total_price = self._has_col("Appointments", "TotalPrice")

        if has_as and has_line_total:
            q = f"""
                SELECT s.{name_col} AS service_name,
                       IFNULL(SUM(asv.ActualPrice), 0) AS revenue
                FROM AppointmentServices asv
                JOIN Services s ON s.ServiceID = asv.ServiceID
                JOIN Appointments a ON a.AppointmentID = asv.AppointmentID
                WHERE a.AppointmentDate >= %s
                  AND a.AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
                GROUP BY s.{name_col}
                ORDER BY revenue DESC;
            """
            rows = self._fetch(q, (start_date, end_date))
            return [(r[0], float(r[1] or 0)) for r in rows]

        if has_appt_serviceid and has_total_price:
            q = f"""
                SELECT s.{name_col} AS service_name,
                       IFNULL(SUM(a.TotalPrice), 0) AS revenue
                FROM Appointments a
                JOIN Services s ON s.ServiceID = a.ServiceID
                WHERE a.AppointmentDate >= %s
                  AND a.AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
                GROUP BY s.{name_col}
                ORDER BY revenue DESC;
            """
            rows = self._fetch(q, (start_date, end_date))
            return [(r[0], float(r[1] or 0)) for r in rows]

        if has_as:
            q = f"""
                SELECT s.{name_col} AS service_name,
                       COUNT(*) AS uses
                FROM AppointmentServices asv
                JOIN Services s ON s.ServiceID = asv.ServiceID
                JOIN Appointments a ON a.AppointmentID = asv.AppointmentID
                WHERE a.AppointmentDate >= %s
                  AND a.AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
                GROUP BY s.{name_col}
                ORDER BY uses DESC;
            """
            rows = self._fetch(q, (start_date, end_date))
            return [(r[0], float(r[1] or 0)) for r in rows]

        return []

    # ---------- KPI Data Loaders ----------
    def get_total_revenue(self, start_date, end_date):
        """Get total revenue from payments in the date range."""
        q = """
            SELECT IFNULL(SUM(Amount), 0) AS total_revenue
            FROM Payments
            WHERE PaymentDate >= %s AND PaymentDate < DATE_ADD(%s, INTERVAL 1 DAY)
        """
        rows = self._fetch(q, (start_date, end_date))
        return float(rows[0][0]) if rows else 0.0
    
    def get_total_appointments(self, start_date, end_date):
        """Get total number of appointments in the date range."""
        q = """
            SELECT COUNT(*) AS total_appointments
            FROM Appointments
            WHERE AppointmentDate >= %s AND AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
        """
        rows = self._fetch(q, (start_date, end_date))
        return int(rows[0][0]) if rows else 0
    
    def get_total_customers(self, start_date, end_date):
        """Get count of unique customers who had appointments in the date range."""
        q = """
            SELECT COUNT(DISTINCT a.CustomerID) AS unique_customers
            FROM Appointments a
            WHERE a.AppointmentDate >= %s AND a.AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
        """
        rows = self._fetch(q, (start_date, end_date))
        return int(rows[0][0]) if rows else 0
    
    def get_completed_appointments(self, start_date, end_date):
        """Get count of completed appointments in the date range."""
        q = """
            SELECT COUNT(*) AS completed_appointments
            FROM Appointments
            WHERE AppointmentDate >= %s AND AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
              AND Status = 'completed'
        """
        rows = self._fetch(q, (start_date, end_date))
        return int(rows[0][0]) if rows else 0
    
    def get_pending_appointments(self, start_date, end_date):
        """Get count of pending/scheduled appointments in the date range."""
        q = """
            SELECT COUNT(*) AS pending_appointments
            FROM Appointments
            WHERE AppointmentDate >= %s AND AppointmentDate < DATE_ADD(%s, INTERVAL 1 DAY)
              AND Status IN ('scheduled', 'pending')
        """
        rows = self._fetch(q, (start_date, end_date))
        return int(rows[0][0]) if rows else 0
    
    def get_top_service_name(self, start_date, end_date):
        """Get the name of the top service by revenue."""
        services = self.load_service_revenue(start_date, end_date)
        if services and len(services) > 0:
            return services[0][0]  # First service name
        return "No Data"
    
    def load_daily_revenue_trend(self, start_date, end_date):
        """Load daily revenue trend data for the date range."""
        q = """
            SELECT DATE(PaymentDate) as payment_date,
                   IFNULL(SUM(Amount), 0) as daily_revenue
            FROM Payments
            WHERE PaymentDate >= %s AND PaymentDate < DATE_ADD(%s, INTERVAL 1 DAY)
            GROUP BY DATE(PaymentDate)
            ORDER BY payment_date ASC
        """
        rows = self._fetch(q, (start_date, end_date))
        return [(str(date), float(revenue)) for date, revenue in rows]

    # ---------- Matplotlib theming ----------
    def _style_fig_ax(self, fig, ax):
        dark = bool(self.get_is_dark())
        fig.patch.set_facecolor(DARK_BG if dark else LIGHT_BG)
        ax.set_facecolor(DARK_AX if dark else LIGHT_AX)
        fg = "#eaeaea" if dark else "#000000"
        grid_c = "#666666" if dark else "#cccccc"
        for spine in ax.spines.values():
            spine.set_color(fg)
        ax.tick_params(colors=fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.title.set_color(fg)
        ax.grid(True, alpha=0.35, color=grid_c)

    # ---------- Charts ----------
    def draw_kpi_metrics(self, start_date, end_date):
        if self.canvas_kpi:
            try:
                self.canvas_kpi.destroy()
            except:
                pass
        
        # Create expanded KPI metrics section - spans both rows
        kpi_frame = ctk.CTkFrame(self.charts_frame)
        kpi_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=6, pady=6)
        
        # Title
        title_label = ctk.CTkLabel(kpi_frame, text="📊 Business Dashboard", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(15, 10))
        
        # Get metrics data
        total_revenue = self.get_total_revenue(start_date, end_date)
        total_appointments = self.get_total_appointments(start_date, end_date)
        avg_appointment_value = total_revenue / max(total_appointments, 1)
        total_customers = self.get_total_customers(start_date, end_date)
        completed_appointments = self.get_completed_appointments(start_date, end_date)
        pending_appointments = self.get_pending_appointments(start_date, end_date)
        top_service = self.get_top_service_name(start_date, end_date)
        
        # Create metrics container (no scroll bar)
        metrics_frame = ctk.CTkFrame(kpi_frame, fg_color="transparent")
        metrics_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Configure grid for metrics (2 columns, multiple rows)
        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # Revenue Metrics Section
        revenue_section = ctk.CTkLabel(metrics_frame, text="💰 REVENUE & FINANCE", 
                                     font=ctk.CTkFont(size=14, weight="bold"), 
                                     text_color="#4CAF50")
        revenue_section.grid(row=row, column=0, columnspan=2, pady=(10, 5), sticky="w")
        row += 1
        
        # Total Revenue
        revenue_card = ctk.CTkFrame(metrics_frame)
        revenue_card.grid(row=row, column=0, sticky="nsew", padx=(0, 5), pady=3)
        ctk.CTkLabel(revenue_card, text="Total Revenue", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(revenue_card, text=f"${total_revenue:,.2f}", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#4CAF50").pack(pady=(0, 8))
        
        # Average Appointment Value
        avg_card = ctk.CTkFrame(metrics_frame)
        avg_card.grid(row=row, column=1, sticky="nsew", padx=(5, 0), pady=3)
        ctk.CTkLabel(avg_card, text="Average Value", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(avg_card, text=f"${avg_appointment_value:.2f}", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#FF9800").pack(pady=(0, 8))
        row += 1
        
        # Appointments Section
        appt_section = ctk.CTkLabel(metrics_frame, text="📅 APPOINTMENTS", 
                                  font=ctk.CTkFont(size=14, weight="bold"), 
                                  text_color="#2196F3")
        appt_section.grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        row += 1
        
        # Total Appointments
        total_appt_card = ctk.CTkFrame(metrics_frame)
        total_appt_card.grid(row=row, column=0, sticky="nsew", padx=(0, 5), pady=3)
        ctk.CTkLabel(total_appt_card, text="Total Appointments", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(total_appt_card, text=f"{total_appointments:,}", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#2196F3").pack(pady=(0, 8))
        
        # Completed Appointments
        completed_card = ctk.CTkFrame(metrics_frame)
        completed_card.grid(row=row, column=1, sticky="nsew", padx=(5, 0), pady=3)
        ctk.CTkLabel(completed_card, text="Completed", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(completed_card, text=f"{completed_appointments:,}", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#4CAF50").pack(pady=(0, 8))
        row += 1
        
        # Pending Appointments (in new row)
        pending_card = ctk.CTkFrame(metrics_frame)
        pending_card.grid(row=row, column=0, sticky="nsew", padx=(0, 5), pady=3)
        ctk.CTkLabel(pending_card, text="Pending/Scheduled", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(pending_card, text=f"{pending_appointments:,}", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#FF9800").pack(pady=(0, 8))
        
        # Completion Rate
        completion_rate = (completed_appointments / max(total_appointments, 1)) * 100
        completion_card = ctk.CTkFrame(metrics_frame)
        completion_card.grid(row=row, column=1, sticky="nsew", padx=(5, 0), pady=3)
        ctk.CTkLabel(completion_card, text="Completion Rate", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(completion_card, text=f"{completion_rate:.1f}%", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#9C27B0").pack(pady=(0, 8))
        row += 1
        
        # Customer & Service Section
        customer_section = ctk.CTkLabel(metrics_frame, text="👥 CUSTOMERS & SERVICES", 
                                      font=ctk.CTkFont(size=14, weight="bold"), 
                                      text_color="#9C27B0")
        customer_section.grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        row += 1
        
        # Total Customers
        customer_card = ctk.CTkFrame(metrics_frame)
        customer_card.grid(row=row, column=0, sticky="nsew", padx=(0, 5), pady=3)
        ctk.CTkLabel(customer_card, text="Unique Customers", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(customer_card, text=f"{total_customers:,}", 
                    font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#9C27B0").pack(pady=(0, 8))
        
        # Top Service
        service_card = ctk.CTkFrame(metrics_frame)
        service_card.grid(row=row, column=1, sticky="nsew", padx=(5, 0), pady=3)
        ctk.CTkLabel(service_card, text="Top Service", 
                    font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        service_text = top_service if len(top_service) <= 15 else top_service[:12] + "..."
        ctk.CTkLabel(service_card, text=service_text, 
                    font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color="#FF5722").pack(pady=(0, 8))
        
        self.canvas_kpi = kpi_frame  # Store reference for cleanup

    def draw_revenue_trend_chart(self, start_date, end_date):
        if self.canvas_right_chart:
            try:
                if hasattr(self.canvas_right_chart, 'get_tk_widget'):
                    self.canvas_right_chart.get_tk_widget().destroy()
                else:
                    self.canvas_right_chart.destroy()
            except:
                pass
        
        # Get daily revenue trend data
        revenue_data = self.load_daily_revenue_trend(start_date, end_date)
        
        fig = Figure(figsize=(5, 6), dpi=100)  # Taller since it spans 2 rows
        ax = fig.add_subplot(111)
        
        if revenue_data:
            dates = [data[0] for data in revenue_data]
            revenues = [data[1] for data in revenue_data]
            
            # Create line plot with markers
            ax.plot(dates, revenues, marker='o', linewidth=2, markersize=6, 
                   color='#4CAF50', markerfacecolor='#4CAF50', markeredgecolor='white')
            
            # Fill area under the curve for visual appeal
            ax.fill_between(dates, revenues, alpha=0.3, color='#4CAF50')
            
            # Format x-axis dates
            if len(dates) > 10:
                # Show every nth date if too many points
                step = max(1, len(dates) // 8)
                ax.set_xticks(range(0, len(dates), step))
                ax.set_xticklabels([dates[i][-5:] for i in range(0, len(dates), step)])  # Show MM-DD
            else:
                ax.set_xticklabels([d[-5:] for d in dates])  # Show MM-DD for all
            
            ax.tick_params(axis='x', rotation=45, labelsize=9)
            
            # Add value annotations on peaks
            max_revenue = max(revenues) if revenues else 0
            if max_revenue > 0:
                max_idx = revenues.index(max_revenue)
                ax.annotate(f'${max_revenue:.0f}', xy=(max_idx, max_revenue), 
                           xytext=(5, 5), textcoords='offset points', 
                           fontsize=8, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        else:
            # No data available
            ax.text(0.5, 0.5, 'No Revenue Data\nfor Selected Period', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, fontweight='bold')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        
        ax.set_title("Daily Revenue Trend", fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Revenue ($)", fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Style the chart
        self._style_fig_ax(fig, ax)
        fig.tight_layout(pad=1.2)
        
        self.canvas_right_chart = FigureCanvasTkAgg(fig, master=self.charts_frame)
        self.canvas_right_chart.draw()
        self.canvas_right_chart.get_tk_widget().grid(row=0, column=1, rowspan=2, sticky="nsew", padx=6, pady=6)

    def draw_service_mix_pie(self, service_rev):
        if self.canvas_right_chart:
            try:
                if hasattr(self.canvas_right_chart, 'get_tk_widget'):
                    self.canvas_right_chart.get_tk_widget().destroy()
                else:
                    self.canvas_right_chart.destroy()
            except:
                pass
        labels = [n if len(n) < 18 else n[:15] + "..." for n, _ in service_rev]
        vals = [v for _, v in service_rev]
        if sum(vals) <= 0:
            labels, vals = ["No Data"], [1]
        fig = Figure(figsize=(4, 3.2), dpi=100)  # Smaller width since moving to right
        ax = fig.add_subplot(111)
        dark = bool(self.get_is_dark())
        text_color = "#eaeaea" if dark else "#000000"
        
        # Create pie chart with white text for dark theme
        wedges, texts, autotexts = ax.pie(vals, labels=labels, autopct="%1.1f%%", 
                                         startangle=90, textprops={'color': text_color})
        
        # Ensure percentage text is also white
        for autotext in autotexts:
            autotext.set_color(text_color)
            autotext.set_fontweight('bold')
        
        ax.set_title("Service Mix (Revenue Share)")
        fig.patch.set_facecolor(DARK_BG if dark else LIGHT_BG)
        ax.set_facecolor(DARK_AX if dark else LIGHT_AX)
        ax.title.set_color(text_color)
        
        fig.tight_layout(pad=1.0)
        self.canvas_right_chart = FigureCanvasTkAgg(fig, master=self.charts_frame)
        self.canvas_right_chart.draw()
        self.canvas_right_chart.get_tk_widget().grid(row=0, column=1, rowspan=2, sticky="nsew", padx=6, pady=6)

    # ---------- Refresh ----------
    def initial_refresh(self):
        """Initial refresh that ensures dates are properly set."""
        # Double-check that dates are set correctly
        if not self.start_entry.get().strip():
            end_default = datetime.today().date()
            start_default = end_default - timedelta(days=90)
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, str(start_default))
        if not self.end_entry.get().strip():
            end_default = datetime.today().date()
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, str(end_default))
        # Now call the regular refresh
        self.refresh_all()
    
    def refresh_all(self):
        start_s = self.start_entry.get().strip()
        end_s = self.end_entry.get().strip()
        try:
            start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
            if end_date < start_date:
                raise ValueError("End date is before start date.")
        except Exception as e:
            messagebox.showerror("Invalid Dates", f"Please use YYYY-MM-DD.\n\n{e}")
            return
        # Draw KPI metrics
        self.draw_kpi_metrics(start_date, end_date)
        
        # Draw selected chart based on dropdown
        selected_chart = self.chart_selector.get()
        if selected_chart == "Revenue Trend":
            self.draw_revenue_trend_chart(start_date, end_date)
        elif selected_chart == "Service Mix":
            services = self.load_service_revenue(start_date, end_date)
            self.draw_service_mix_pie(services)

    # ---------- Public API ----------
    def set_dark_mode_getter(self, get_is_dark):
        self.get_is_dark = get_is_dark
        self.refresh_all()