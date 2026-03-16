import tkinter as tk
from models import ParkingGarage
from gui import GarageGUI

if __name__ == "__main__":
    root = tk.Tk()
    # Initialize a garage with 200 spots (5 levels * 40 spots/level)
    garage_system = ParkingGarage(200)
    app = GarageGUI(root, garage_system)
    root.mainloop()