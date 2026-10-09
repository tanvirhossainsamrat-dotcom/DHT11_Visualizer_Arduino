import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import collections
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ArduinoDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("DHT11 Sensor Dashboard")
        self.root.geometry("850x700")
        self.root.configure(bg="#f4f7f6")
        
        self.serial_port = None
        self.is_connected = False
        
        self.max_data_points = 20
        self.times = collections.deque(maxlen=self.max_data_points)
        self.temps = collections.deque(maxlen=self.max_data_points)
        self.hums = collections.deque(maxlen=self.max_data_points)
        
        self.target_temp = 0.0
        self.target_hum = 0.0
        self.display_temp = 0.0
        self.display_hum = 0.0
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.animate_labels()

    def setup_ui(self):
        self.status_label = tk.Label(self.root, text="Status: Disconnected", bg="#f4f7f6", fg="#666", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side=tk.TOP, anchor="nw", padx=15, pady=10)
        
        # --- Header Section ---
        header_frame = tk.Frame(self.root, bg="#f4f7f6")
        header_frame.pack(pady=10)
        
        tk.Label(header_frame, text="Select Port:", bg="#f4f7f6", font=("Segoe UI", 12)).pack(side=tk.LEFT, padx=10)
        
        self.port_combo = ttk.Combobox(header_frame, values=self.get_serial_ports(), width=15)
        self.port_combo.pack(side=tk.LEFT, padx=10)
        if self.port_combo['values']:
            self.port_combo.current(0)
            
        self.connect_btn = tk.Button(header_frame, text="Connect to Arduino", bg="#007bff", fg="white", 
                                     font=("Segoe UI", 11, "bold"), relief=tk.FLAT, padx=15, pady=5, 
                                     command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        # --- Cards Section ---
        cards_frame = tk.Frame(self.root, bg="#f4f7f6")
        cards_frame.pack(pady=10)
        
        temp_card = tk.Frame(cards_frame, bg="white", padx=30, pady=20, relief=tk.RIDGE, bd=2)
        temp_card.pack(side=tk.LEFT, padx=20)
        tk.Label(temp_card, text="Temperature", bg="white", fg="#666", font=("Segoe UI", 12)).pack()
        self.temp_label = tk.Label(temp_card, text="0.0 °C", bg="white", fg="#ff6384", font=("Segoe UI", 24, "bold"))
        self.temp_label.pack(pady=10)
        
        hum_card = tk.Frame(cards_frame, bg="white", padx=30, pady=20, relief=tk.RIDGE, bd=2)
        hum_card.pack(side=tk.LEFT, padx=20)
        tk.Label(hum_card, text="Humidity", bg="white", fg="#666", font=("Segoe UI", 12)).pack()
        self.hum_label = tk.Label(hum_card, text="0.0 %", bg="white", fg="#36a2eb", font=("Segoe UI", 24, "bold"))
        self.hum_label.pack(pady=10)

        # --- Graph Section ---
        graph_frame = tk.Frame(self.root, bg="white", relief=tk.RIDGE, bd=2)
        graph_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.fig.patch.set_facecolor('white')
        
        self.temp_line, = self.ax.plot([], [], color='#ff6384', label='Temperature (°C)', marker='o')
        self.hum_line, = self.ax.plot([], [], color='#36a2eb', label='Humidity (%)', marker='o')
        
        self.ax.legend()
        self.ax.set_facecolor('#fdfdfd')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def toggle_connection(self):
        if not self.is_connected:
            selected_port = self.port_combo.get()
            if not selected_port:
                messagebox.showerror("Error", "Please select a COM port first.")
                return
            
            try:
                self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="Disconnect", bg="#dc3545")
                self.port_combo.config(state="disabled")
                self.status_label.config(text="Status: Connected. Waiting for data...", fg="#2ecc71")
                
                self.times.clear()
                self.temps.clear()
                self.hums.clear()
                
                current_time = datetime.now().strftime('%H:%M:%S')
                self.times.append(current_time)
                self.temps.append(0.0)
                self.hums.append(0.0)
                
                self.target_temp = 0.0
                self.target_hum = 0.0
                self.display_temp = 0.0
                self.display_hum = 0.0
                self.temp_label.config(text="0.0 °C")
                self.hum_label.config(text="0.0 %")
                
                self.update_graph()
                
                self.root.after(100, self.read_serial_data)
                
            except serial.SerialException as e:
                messagebox.showerror("Connection Error", f"Close Arduino IDE Serial Monitor!\n\n{e}")
        else:
            self.disconnect()

    def disconnect(self):
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connect_btn.config(text="Connect to Arduino", bg="#007bff")
        self.port_combo.config(state="readonly")
        self.status_label.config(text="Status: Disconnected", fg="#666")

    def read_serial_data(self):
        if self.is_connected and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    print(f"Arduino says: {raw_line}") 
                    
                    if "Temp:" in raw_line and "Humidity:" in raw_line:
                        try:
                            parts = raw_line.split(',')
                            temp_value = float(parts[0].split(':')[1])
                            hum_value = float(parts[1].split(':')[1])
                            
                            self.status_label.config(text="Status: Receiving Data Active", fg="#2ecc71")
                            self.update_dashboard(temp_value, hum_value)
                                
                        except Exception as e:
                            print(f"Skipping broken line: {raw_line}")
            except Exception as e:
                print(f"Read error: {e}")
                self.disconnect()
                
            self.root.after(100, self.read_serial_data)

    def update_dashboard(self, temp, hum):
        self.target_temp = temp
        self.target_hum = hum
        
        current_time = datetime.now().strftime('%H:%M:%S')
        self.times.append(current_time)
        self.temps.append(temp)
        self.hums.append(hum)
        
        self.update_graph()
        
    def update_graph(self):
        self.temp_line.set_data(range(len(self.times)), self.temps)
        self.hum_line.set_data(range(len(self.times)), self.hums)
        
        self.ax.set_xlim(0, max(self.max_data_points - 1, len(self.times) - 1))
        
        # Lock Y-axis from 0 to 100
        self.ax.set_ylim(0, 100)
        self.ax.set_yticks(range(0, 101, 10))
        
        self.ax.set_xticks(range(len(self.times)))
        self.ax.set_xticklabels(self.times, rotation=45, ha='right', fontsize=8)
        
        self.fig.tight_layout()
        self.canvas.draw()
        
    def animate_labels(self):
        if self.is_connected:
            diff_t = self.target_temp - self.display_temp
            diff_h = self.target_hum - self.display_hum
            
            # 1000ms duration at 50ms interval = 20 steps. 
            # Calculate a linear step size so the initial climb takes exactly 1 second.
            step_t = max(abs(self.target_temp / 20.0), 0.5)
            step_h = max(abs(self.target_hum / 20.0), 0.5)
            
            # Animate Temperature
            if abs(diff_t) > step_t:
                self.display_temp += step_t if diff_t > 0 else -step_t
            else:
                self.display_temp = self.target_temp
                
            # Animate Humidity
            if abs(diff_h) > step_h:
                self.display_hum += step_h if diff_h > 0 else -step_h
            else:
                self.display_hum = self.target_hum
                
            self.temp_label.config(text=f"{self.display_temp:.1f} °C")
            self.hum_label.config(text=f"{self.display_hum:.1f} %")
                
        self.root.after(50, self.animate_labels)

    def on_closing(self):
        self.disconnect()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ArduinoDashboard(root)
    root.mainloop()