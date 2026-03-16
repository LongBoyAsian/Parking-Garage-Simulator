import time

class Vehicle:
    """Base class for a vehicle. Should not be instantiated directly."""
    rate_multiplier = 1.0
    type = "Vehicle"

    def __init__(self, license_plate):
        if type(self) is Vehicle:
            raise NotImplementedError("Vehicle is an abstract class and cannot be instantiated directly")
        self.license_plate = license_plate
        self.entry_time = time.time()

class Car(Vehicle):
    """Represents a car with a standard rate."""
    rate_multiplier = 1.0
    type = "Car"

class Motorcycle(Vehicle):
    """Represents a motorcycle with a discounted rate."""
    rate_multiplier = 0.75
    type = "Motorcycle"

class Truck(Vehicle):
    """Represents a truck with a premium rate."""
    rate_multiplier = 1.5
    type = "Truck"

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
        Uses the vehicle's specific rate multiplier and real-world time.
        Also implements dynamic 'surge' pricing based on capacity.
        """
        elapsed_seconds = time.time() - vehicle.entry_time
        elapsed_hours = elapsed_seconds / 3600
        hours_charged = max(1.0, round(elapsed_hours, 2)) # Charge at least 1 hour
        
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