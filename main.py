import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import time
import re

class Vehicle:
    """Represents a vehicle with a license plate and entry timestamp."""
    def __init__(self, license_plate):
        self.license_plate = license_plate
        self.entry_time = time.time()

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

    def get_available_spots(self):
        return sorted(list(self.available_spots))

    def park_vehicle(self, license_plate):
        license_plate = license_plate.strip().upper()
        if license_plate in self.active_plates:
            return -1 # Indicate already parked

        if not self.available_spots:
            return None
        
        spot_id = min(self.available_spots)
        self.spots[spot_id].park_vehicle(Vehicle(license_plate))
        self.available_spots.remove(spot_id)
        self.active_plates.add(license_plate)
        return spot_id

    def calculate_price(self, entry_time):
        """
        Calculates price based on time spent. 
        Time is sped up for simulation (1 real second = 100 simulated seconds).
        Also implements dynamic 'surge' pricing based on capacity.
        """
        elapsed_seconds = time.time() - entry_time
        simulated_hours = (elapsed_seconds * 100) / 3600  
        hours_charged = max(1.0, round(simulated_hours, 2)) # Charge at least 1 hour
        
        # Dynamic multiplier: surge pricing if garage is heavily occupied
        available_spots = len(self.available_spots)
        total_spots = len(self.spots)
        occupancy_rate = (total_spots - available_spots) / total_spots
        
        multiplier = 1.5 if occupancy_rate >= 0.8 else 1.0
        
        return hours_charged * self.base_rate * multiplier

    def checkout_vehicle(self, spot_id):
        spot = self.spots.get(spot_id)
        if spot and not spot.is_available():
            vehicle = spot.remove_vehicle()
            self.available_spots.add(spot_id)
            self.active_plates.remove(vehicle.license_plate)
            cost = self.calculate_price(vehicle.entry_time)
            return vehicle.license_plate, cost
        return None, 0

class GarageGUI:
    """Graphical interface for the Parking Garage Simulator."""
    def __init__(self, root, garage):
        self.root = root
        self.garage = garage
        self.root.title("Parking Garage Simulator")
        
        self.buttons = {}
        self.create_widgets()

    def create_widgets(self):
        # Notebook for parking levels
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=20, padx=20, expand=True, fill="both")

        spots = list(self.garage.spots.keys())
        spots_per_level = len(spots) // 5 if len(spots) >= 5 else len(spots)
        
        for level in range(1, 6):
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Level {level}")
            
            # Get the spots for this specific level
            start_idx = (level - 1) * spots_per_level
            end_idx = start_idx + spots_per_level
            level_spots = spots[start_idx:end_idx]
            
            half = len(level_spots) // 2 + len(level_spots) % 2
            
            for i, spot_id in enumerate(level_spots):
                if i < half:
                    row, col = i, 0
                else:
                    row, col = i - half, 2
                    
                btn = tk.Button(frame, text=f"Spot {spot_id}\n[Empty]", 
                                width=15, height=3, bg="lightgreen",
                                command=lambda s=spot_id: self.handle_spot_click(s))
                btn.grid(row=row, column=col, padx=5, pady=5)
                self.buttons[spot_id] = btn
                
            # Create the driving aisle (vertical)
            aisle_text = "↑\n\nA\nI\nS\nL\nE\n\n↓"
            aisle = tk.Label(frame, text=aisle_text, bg="darkgray", fg="white", font=("Helvetica", 12, "bold"), width=10)
            aisle.grid(row=0, column=1, rowspan=max(1, half), sticky="ns", padx=20)

        # Control Panel
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=10)

        self.park_btn = tk.Button(self.control_frame, text="Park New Vehicle", command=self.park_vehicle, bg="lightblue")
        self.park_btn.pack(side=tk.LEFT, padx=10)

    def update_ui(self):
        """Refresh the colors and text of the spots based on real-time data."""
        for spot_id, spot in self.garage.spots.items():
            if spot.is_available():
                self.buttons[spot_id].config(text=f"Spot {spot_id}\n[Empty]", bg="lightgreen")
            else:
                self.buttons[spot_id].config(text=f"Spot {spot_id}\n[{spot.vehicle.license_plate}]", bg="salmon")

    def park_vehicle(self):
        plate = simpledialog.askstring("Input", "Enter License Plate:", parent=self.root)
        if plate:
            # Validate US license plate (1 to 8 characters long, containing letters and numbers 0-9)
            cleaned_plate = re.sub(r'[\s\-]', '', plate)
            if not re.match(r'^[A-Za-z0-9]{1,8}$', cleaned_plate):
                messagebox.showwarning("Invalid Plate", "Please enter a valid US license plate (1 to 8 characters long, letters and numbers only).")
                return

            spot_id = self.garage.park_vehicle(plate)
            if spot_id == -1:
                messagebox.showwarning("Duplicate", f"Vehicle '{plate.strip().upper()}' is already parked!")
            elif spot_id is not None:
                messagebox.showinfo("Success", f"Vehicle parked at Spot {spot_id}")
                self.update_ui()
            else:
                messagebox.showwarning("Full", "The parking garage is currently full!")

    def handle_spot_click(self, spot_id):
        """Handles clicking a specific spot to checkout the vehicle."""
        spot = self.garage.spots[spot_id]
        if not spot.is_available():
            if messagebox.askyesno("Checkout", f"Checkout vehicle {spot.vehicle.license_plate} from Spot {spot_id}?"):
                plate, cost = self.garage.checkout_vehicle(spot_id)
                messagebox.showinfo("Receipt", f"Vehicle {plate} checked out.\nTotal Cost: ${cost:.2f}")
                self.update_ui()
        else:
            messagebox.showinfo("Info", "This spot is empty. Use 'Park New Vehicle' to assign a car here.")

if __name__ == "__main__":
    root = tk.Tk()
    # Initialize a garage with 50 spots (10 per level)
    garage_system = ParkingGarage(50)
    app = GarageGUI(root, garage_system)
    root.mainloop()