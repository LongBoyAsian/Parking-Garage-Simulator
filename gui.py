import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import re
import time

from models import Car, Motorcycle, Truck

class VehicleInputDialog(simpledialog.Dialog):
    """Custom dialog to get vehicle license plate and type."""
    def body(self, master):
        master.configure(bg='lightgrey')
        tk.Label(master, text="License Plate:", bg='lightgrey').grid(row=0, padx=5, pady=5, sticky="w")
        tk.Label(master, text="Vehicle Type:", bg='lightgrey').grid(row=1, padx=5, pady=5, sticky="w")

        self.plate_entry = tk.Entry(master)
        self.plate_entry.grid(row=0, column=1, padx=5, pady=5)

        self.vehicle_type = tk.StringVar(master)
        self.vehicle_type.set("Car") # default value
        self.type_menu = tk.OptionMenu(master, self.vehicle_type, "Car", "Motorcycle", "Truck")
        self.type_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        return self.plate_entry # initial focus

    def apply(self):
        self.result = (self.plate_entry.get(), self.vehicle_type.get())

class GarageGUI:
    """Graphical interface for the Parking Garage Simulator."""
    def __init__(self, root, garage):
        self.root = root
        self.garage = garage
        self.root.title("Parking Garage Simulator")
        self.DARK_BG = "darkgray"
        self.root.configure(bg=self.DARK_BG)

        # Style for ttk widgets for a dark theme
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TNotebook", background=self.DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#555555", foreground="white", borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", self.DARK_BG)], foreground=[("selected", "yellow")])
        
        self.buttons = {}
        self.create_widgets()
        # Start the periodic update loop for real-time costs
        self.update_costs_periodically()

    def create_widgets(self):
        # Notebook for parking levels
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        spots = list(self.garage.spots.keys())
        spots_per_level = 40
        spots_per_column = 10

        for level in range(1, 6):
            level_frame = tk.Frame(self.notebook, bg=self.DARK_BG)
            self.notebook.add(level_frame, text=f"Level {level}")

            spot_grid_frame = tk.Frame(level_frame, bg=self.DARK_BG)
            spot_grid_frame.pack(expand=True)

            start_idx = (level - 1) * spots_per_level
            end_idx = start_idx + spots_per_level
            level_spots = spots[start_idx:end_idx]

            for i, spot_id in enumerate(level_spots):
                column_index = i // spots_per_column
                row = i % spots_per_column

                if column_index == 0: grid_column = 0
                elif column_index == 1: grid_column = 2
                elif column_index == 2: grid_column = 3
                else: grid_column = 5

                # Create a frame to act as the custom border
                border_frame = tk.Frame(spot_grid_frame, bg='white')
                
                # Adjust padding to close the gap between the middle two columns
                if grid_column == 2:
                    border_frame.grid(row=row, column=grid_column, padx=(5, 0), pady=2)
                elif grid_column == 3:
                    border_frame.grid(row=row, column=grid_column, padx=(0, 5), pady=2)
                else:
                    border_frame.grid(row=row, column=grid_column, padx=5, pady=2)

                btn = tk.Button(border_frame, text=f"Spot {spot_id}\n[Empty]",
                                width=18, height=4, bg="lightgreen",
                                command=lambda s=spot_id: self.handle_spot_click(s),
                                relief='flat', borderwidth=0, highlightthickness=0)
                self.buttons[spot_id] = btn

                # Apply padding inside the frame to create the 3-sided border effect
                border_thickness = 4
                if grid_column == 0:  # Leftmost column, aisle on right
                    btn.pack(padx=(border_thickness, 0), pady=border_thickness)
                elif grid_column == 2: # Middle-left column, touching middle
                    btn.pack(padx=(0, border_thickness // 2), pady=border_thickness)
                elif grid_column == 3: # Middle-right column, touching middle
                    btn.pack(padx=(border_thickness // 2, 0), pady=border_thickness)
                else:  # Rightmost column (grid_column == 5), aisle on left
                    btn.pack(padx=(0, border_thickness), pady=border_thickness)

            exit_aisle_text = "EXIT\n\n⬇"
            aisle1 = tk.Label(spot_grid_frame, text=exit_aisle_text, bg=self.DARK_BG, fg="white", font=("Helvetica", 12, "bold"), width=10)
            aisle1.grid(row=0, column=1, rowspan=spots_per_column, sticky="ns", padx=20)

            enter_aisle_text = "⬆\n\nENTER"
            aisle2 = tk.Label(spot_grid_frame, text=enter_aisle_text, bg=self.DARK_BG, fg="white", font=("Helvetica", 12, "bold"), width=10)
            aisle2.grid(row=0, column=4, rowspan=spots_per_column, sticky="ns", padx=20)

        # --- Bottom Panel ---
        bottom_frame = tk.Frame(self.root, bg=self.DARK_BG)
        bottom_frame.pack(pady=10, padx=10, fill="x", side=tk.BOTTOM)

        # Control Panel
        self.control_frame = tk.Frame(bottom_frame, bg=self.DARK_BG)
        self.control_frame.pack(side=tk.LEFT, padx=10, anchor="w")

        self.park_btn = tk.Button(self.control_frame, text="Park New Vehicle", command=self.park_vehicle, bg="lightblue")
        self.park_btn.pack(side=tk.LEFT, padx=10)

        self.revenue_label = tk.Label(self.control_frame, text="Total Revenue: $0.00", font=("Helvetica", 12, "bold"), bg=self.DARK_BG, fg="white")
        self.revenue_label.pack(side=tk.LEFT, padx=(20, 5))

        self.occupancy_label = tk.Label(self.control_frame, text="", font=("Helvetica", 12, "bold"), bg=self.DARK_BG, fg="white")
        self.occupancy_label.pack(side=tk.LEFT, padx=(5, 20))

        # --- Info Panel (Timer and Pricing) ---
        info_frame = tk.Frame(bottom_frame, bg=self.DARK_BG)
        info_frame.pack(side=tk.RIGHT, padx=20, anchor="e")

        self.timer_label = tk.Label(info_frame, text="Current Time: ", font=("Courier", 12), bg=self.DARK_BG, fg="white")
        self.timer_label.pack(anchor="w")

        pricing_frame = tk.LabelFrame(info_frame, text="Pricing Information", bg=self.DARK_BG, fg="white", font=("Helvetica", 10, "bold"))
        pricing_frame.pack(pady=5, fill="x")

        # Base Rate
        base_rate_frame = tk.Frame(pricing_frame, bg=self.DARK_BG)
        base_rate_frame.pack(anchor="w", padx=5)
        tk.Label(base_rate_frame, text="Base Rate:", font=("Helvetica", 10, "bold"), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)
        tk.Label(base_rate_frame, text=f" ${self.garage.base_rate:.2f} / hour", font=("Helvetica", 10), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)

        # Motorcycle
        motorcycle_frame = tk.Frame(pricing_frame, bg=self.DARK_BG)
        motorcycle_frame.pack(anchor="w", padx=5)
        tk.Label(motorcycle_frame, text="Motorcycle:", font=("Helvetica", 10, "bold"), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)
        tk.Label(motorcycle_frame, text=f" ${self.garage.base_rate * Motorcycle.rate_multiplier:.2f} / hr ({Motorcycle.rate_multiplier}x)", font=("Helvetica", 10), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)

        # Car
        car_frame = tk.Frame(pricing_frame, bg=self.DARK_BG)
        car_frame.pack(anchor="w", padx=5)
        tk.Label(car_frame, text="Car:", font=("Helvetica", 10, "bold"), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)
        tk.Label(car_frame, text=f" ${self.garage.base_rate * Car.rate_multiplier:.2f} / hr ({Car.rate_multiplier}x)", font=("Helvetica", 10), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)

        # Truck
        truck_frame = tk.Frame(pricing_frame, bg=self.DARK_BG)
        truck_frame.pack(anchor="w", padx=5)
        tk.Label(truck_frame, text="Truck:", font=("Helvetica", 10, "bold"), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)
        tk.Label(truck_frame, text=f" ${self.garage.base_rate * Truck.rate_multiplier:.2f} / hr ({Truck.rate_multiplier}x)", font=("Helvetica", 10), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)

        # Surge
        surge_frame = tk.Frame(pricing_frame, bg=self.DARK_BG)
        surge_frame.pack(anchor="w", padx=5)
        tk.Label(surge_frame, text="Surge (>=80%):", font=("Helvetica", 10, "bold"), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)
        tk.Label(surge_frame, text=" 1.5x", font=("Helvetica", 10), bg=self.DARK_BG, fg="white").pack(side=tk.LEFT)

        self.update_status_bar()

    def update_status_bar(self):
        """Updates the revenue and occupancy labels in the control panel."""
        total_spots = len(self.garage.spots)
        occupied = total_spots - len(self.garage.available_spots)
        occupancy_pct = (occupied / total_spots) * 100 if total_spots > 0 else 0

        self.revenue_label.config(text=f"Total Revenue: ${self.garage.total_revenue:.2f}")
        self.occupancy_label.config(text=f"| Occupancy: {occupied}/{total_spots} ({occupancy_pct:.1f}%)")

    def update_ui(self):
        """Refresh the colors and text of the spots based on real-time data."""
        for spot_id, spot in self.garage.spots.items():
            button = self.buttons[spot_id]
            if spot.is_available():
                button.config(text=f"Spot {spot_id}\n[Empty]", bg="lightgreen")
            else:
                # Set initial text and color. The cost will be added by the periodic update.
                button.config(text=f"Spot {spot_id}\n[{spot.vehicle.license_plate}]\n({spot.vehicle.type})", bg="salmon")

    def update_costs_periodically(self):
        """Periodically updates the cost display and simulated timer."""
        for spot_id, spot in self.garage.spots.items():
            if not spot.is_available():
                current_cost = self.garage.calculate_price(spot.vehicle)
                self.buttons[spot_id].config(
                    text=f"Spot {spot_id}\n[{spot.vehicle.license_plate}]\n({spot.vehicle.type}) ${current_cost:.2f}"
                )

        # Update real-time clock
        current_time_str = time.strftime("%I:%M:%S %p") # e.g., 02:30:55 PM
        self.timer_label.config(text=f"Current Time: {current_time_str}")
        # Schedule the next update in 1000ms (1 second)
        self.root.after(1000, self.update_costs_periodically)
    def park_vehicle(self):
        dialog = VehicleInputDialog(self.root, "Park Vehicle")
        if dialog.result:
            plate, vehicle_type = dialog.result
            if not plate:
                messagebox.showwarning("Input Error", "License plate cannot be empty.")
                return

            # Validate US license plate (1 to 8 characters long, containing letters and numbers 0-9)
            cleaned_plate = re.sub(r'[\s\-]', '', plate)
            if not re.match(r'^[A-Za-z0-9]{1,8}$', cleaned_plate):
                messagebox.showwarning("Invalid Plate", "Please enter a valid US license plate (1 to 8 characters long, letters and numbers only).")
                return

            spot_id = self.garage.park_vehicle(plate, vehicle_type)
            if spot_id == -1:
                messagebox.showwarning("Duplicate", f"Vehicle '{plate.strip().upper()}' is already parked!")
            elif spot_id is not None:
                messagebox.showinfo("Success", f"Vehicle parked at Spot {spot_id}")
                self.update_ui()
                self.update_status_bar()
                
                # Switch to the level where the car was parked
                spots_per_level = 40
                level_index = (spot_id - 1) // spots_per_level
                self.notebook.select(level_index)
            else:
                messagebox.showwarning("Full", "The parking garage is currently full!")

    def handle_spot_click(self, spot_id):
        """Handles clicking a specific spot to checkout the vehicle."""
        spot = self.garage.spots[spot_id]
        if not spot.is_available():
            # Calculate final cost for the confirmation dialog
            final_cost = self.garage.calculate_price(spot.vehicle)
            if messagebox.askyesno("Checkout", f"Checkout vehicle {spot.vehicle.license_plate} ({spot.vehicle.type}) from Spot {spot_id}?\n\nCurrent Cost: ${final_cost:.2f}"):
                plate, cost = self.garage.checkout_vehicle(spot_id)
                messagebox.showinfo("Receipt", f"Vehicle {plate} checked out.\nTotal Cost: ${cost:.2f}")
                self.update_ui()
                self.update_status_bar()
        else:
            messagebox.showinfo("Info", "This spot is empty. Use 'Park New Vehicle' to assign a car here.")