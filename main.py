import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import time
import re

class Vehicle:
    """Base class for a vehicle. Should not be instantiated directly."""
    def __init__(self, license_plate):
        if type(self) is Vehicle:
            raise NotImplementedError("Vehicle is an abstract class and cannot be instantiated directly")
        self.license_plate = license_plate
        self.entry_time = time.time()
        self.rate_multiplier = 1.0
        self.type = "Vehicle"

class Car(Vehicle):
    """Represents a car with a standard rate."""
    def __init__(self, license_plate):
        super().__init__(license_plate)
        self.rate_multiplier = 1.0
        self.type = "Car"

class Motorcycle(Vehicle):
    """Represents a motorcycle with a discounted rate."""
    def __init__(self, license_plate):
        super().__init__(license_plate)
        self.rate_multiplier = 0.75
        self.type = "Motorcycle"

class Truck(Vehicle):
    """Represents a truck with a premium rate."""
    def __init__(self, license_plate):
        super().__init__(license_plate)
        self.rate_multiplier = 1.5
        self.type = "Truck"

class ParkingSpot:
    """Represents a single parking spot."""
    def __init__(self, spot_id):
        self.spot_id = spot_id
        self.vehicle = None

    def is_available(self):
        return self.vehicle is None

    def park_vehicle(self, vehicle):
        self.vehicle = vehicle

    def remove_vehicle(self):
        vehicle = self.vehicle
        self.vehicle = None
        return vehicle

class ParkingGarage:
    """Manages the parking spots, availability, and pricing logic."""
    def __init__(self, num_spots):
        # Dictionary to track spots for O(1) lookups
        self.spots = {i: ParkingSpot(i) for i in range(1, num_spots + 1)}
        # Sets to handle true O(1) lookups for availability and uniqueness
        self.available_spots = set(range(1, num_spots + 1))
        self.active_plates = set()
        self.base_rate = 5.0 # Base price per hour
        self.total_revenue = 0.0

    def get_available_spots(self):
        return sorted(list(self.available_spots))

    def park_vehicle(self, license_plate, vehicle_type="Car"):
        license_plate = license_plate.strip().upper()
        if license_plate in self.active_plates:
            return -1 # Indicate already parked

        if not self.available_spots:
            return None

        vehicle_map = {"Car": Car, "Motorcycle": Motorcycle, "Truck": Truck}
        vehicle_class = vehicle_map.get(vehicle_type, Car)
        new_vehicle = vehicle_class(license_plate)

        spot_id = min(self.available_spots)
        self.spots[spot_id].park_vehicle(new_vehicle)
        self.available_spots.remove(spot_id)
        self.active_plates.add(license_plate)
        return spot_id

    def calculate_price(self, vehicle):
        """
        Calculates price based on time spent. 
        Uses the vehicle's specific rate multiplier.
        Time is sped up for simulation (1 real second = 100 simulated seconds).
        Also implements dynamic 'surge' pricing based on capacity.
        """
        elapsed_seconds = time.time() - vehicle.entry_time
        simulated_hours = (elapsed_seconds * 100) / 3600  
        hours_charged = max(1.0, round(simulated_hours, 2)) # Charge at least 1 hour
        
        # Dynamic multiplier: surge pricing if garage is heavily occupied
        available_spots = len(self.available_spots)
        total_spots = len(self.spots)
        occupancy_rate = (total_spots - available_spots) / total_spots
        
        multiplier = 1.5 if occupancy_rate >= 0.8 else 1.0
        
        return hours_charged * self.base_rate * vehicle.rate_multiplier * multiplier

    def checkout_vehicle(self, spot_id):
        spot = self.spots.get(spot_id)
        if spot and not spot.is_available():
            vehicle = spot.remove_vehicle()
            self.available_spots.add(spot_id)
            self.active_plates.remove(vehicle.license_plate)
            cost = self.calculate_price(vehicle)
            self.total_revenue += cost
            return vehicle.license_plate, cost
        return None, 0

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

        # Control Panel
        self.control_frame = tk.Frame(self.root, bg=self.DARK_BG)
        self.control_frame.pack(pady=10)

        self.park_btn = tk.Button(self.control_frame, text="Park New Vehicle", command=self.park_vehicle, bg="lightblue")
        self.park_btn.pack(side=tk.LEFT, padx=10)

        self.revenue_label = tk.Label(self.control_frame, text="Total Revenue: $0.00", font=("Helvetica", 12, "bold"), bg=self.DARK_BG, fg="white")
        self.revenue_label.pack(side=tk.LEFT, padx=(20, 5))

        self.occupancy_label = tk.Label(self.control_frame, text="", font=("Helvetica", 12, "bold"), bg=self.DARK_BG, fg="white")
        self.occupancy_label.pack(side=tk.LEFT, padx=(5, 20))

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
        """Periodically updates the cost display for all parked vehicles."""
        for spot_id, spot in self.garage.spots.items():
            if not spot.is_available():
                current_cost = self.garage.calculate_price(spot.vehicle)
                self.buttons[spot_id].config(
                    text=f"Spot {spot_id}\n[{spot.vehicle.license_plate}]\n({spot.vehicle.type}) ${current_cost:.2f}"
                )
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

if __name__ == "__main__":
    root = tk.Tk()
    # Initialize a garage with 200 spots (5 levels * 40 spots/level)
    garage_system = ParkingGarage(200)
    app = GarageGUI(root, garage_system)
    root.mainloop()