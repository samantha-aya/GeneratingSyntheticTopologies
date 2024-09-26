import tkinter as tk
from tkinter import ttk
import GenerateGraph  # Import the second code
import os

# Function to delete only "radial.pdf" from the "Output\\Regulatory" folder
def delete_radial_pdf():
    regulatory_folder = "Output\\Regulatory"
    radial_pdf_path = os.path.join(regulatory_folder, "radial.pdf")
    if os.path.exists(radial_pdf_path):
        try:
            os.unlink(radial_pdf_path)  # Delete only "radial.pdf"
            print(f"{radial_pdf_path} has been deleted.")
        except Exception as e:
            print(f"Failed to delete {radial_pdf_path}. Reason: {e}")

# Function to open the newly created radial.pdf after it has been generated
def open_radial_pdf():
    regulatory_folder = "Output\\Regulatory"
    radial_pdf_path = os.path.join(regulatory_folder, "radial.pdf")
    if os.path.exists(radial_pdf_path):
        try:
            os.startfile(radial_pdf_path)  # Open the PDF file
            print(f"{radial_pdf_path} has been opened.")
        except Exception as e:
            print(f"Failed to open {radial_pdf_path}. Reason: {e}")
    else:
        print(f"{radial_pdf_path} not found after generation.")

# Function to run the graph code with the selected code_to_run value
def run_graph(code_to_run):
    GenerateGraph.main(code_to_run, [])
    open_radial_pdf()  # Open the radial.pdf after generating it

# Create the Tkinter window
root = tk.Tk()
root.geometry('370x100')  # Set the size of the window

# Label for visual output
visualSelection = tk.Label(text="Visual Output:")
visualSelection.pack()
visualSelection.place(x=140, y=15)  # Want it top and middle

# Function for WAN Button
def on_wan_button():
    delete_radial_pdf()  # Delete "radial.pdf" before running the code
    run_graph(2)  # Set code_to_run to 2 (e.g., Generate WAN graph)

# Function for LAN - Substation Button
def on_util_button():
    run_graph(3)  # Set code_to_run to 3 (e.g., generate utility internal layout)

# Function for LAN - Utility Button
def on_sub_button():
    run_graph(1)  # Set code_to_run to 1 (e.g., generate substation internal layout)

# WAN Button
wanButton = tk.Button(
    text="WAN",
    width=13,
    height=1,
    bg="gray",
    fg="white",
    command=on_wan_button  # Call on_wan_button when clicked
)
wanButton.pack()
wanButton.place(x=10, y=50)

# LAN - Utility Button
utilButton = tk.Button(
    text="LAN - Utility",
    width=13,
    height=1,
    bg="gray",
    fg="white",
    command=on_util_button  # Call on_util_button when clicked
)
utilButton.pack()
utilButton.place(x=130, y=50)

# LAN - Substation Button
subButton = tk.Button(
    text="LAN - Substation",
    width=13,
    height=1,
    bg="gray",
    fg="white",
    command=on_sub_button  # Call on_sub_button when clicked
)
subButton.pack()
subButton.place(x=250, y=50)

root.mainloop()
