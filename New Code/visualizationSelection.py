import tkinter as tk
import GenerateGraph  #import the second code
import os

#function to delete only "radial.pdf" from the "Output\\Regulatory" folder
def delete_radial_pdf():
    regulatory_folder = "Output\\Regulatory"
    radial_pdf_path = os.path.join(regulatory_folder, "radial.pdf")
    if os.path.exists(radial_pdf_path):
        try:
            os.unlink(radial_pdf_path)  #delete "radial.pdf" because it wont work
            print(f"{radial_pdf_path} has been deleted.")
        except Exception as e:
            print(f"Failed to delete {radial_pdf_path}. Reason: {e}")

#function to open the newly created radial.pdf after it has been generated
def open_radial_pdf():
    regulatory_folder = "Output\\Regulatory"
    radial_pdf_path = os.path.join(regulatory_folder, "radial.pdf")
    if os.path.exists(radial_pdf_path):
        try:
            os.startfile(radial_pdf_path)  #open the PDF file
            print(f"{radial_pdf_path} has been opened.")
        except Exception as e:
            print(f"Failed to open {radial_pdf_path}. Reason: {e}")
    else:
        print(f"{radial_pdf_path} not found after generation.")

#function to run the graph code with the selected code_to_run value
def run_graph(code_to_run):
    GenerateGraph.main(code_to_run, [])
    open_radial_pdf()  #open the radial.pdf after generating it

#create the Tkinter window
root = tk.Tk()
root.geometry('370x100')  #set the size of the window

#label for visual output
visualSelection = tk.Label(text="Visual Output:")
visualSelection.pack()
visualSelection.place(x=140, y=15)  #want it top and middle

#function for WAN Button
def on_wan_button():
    delete_radial_pdf()  #delete "radial.pdf" before running the code
    run_graph(2)  #set code_to_run to 2 (e.g., Generate WAN graph)

# Function for LAN - Substation Button
def on_util_button():
    run_graph(3)  #set code_to_run to 3 (e.g., generate utility internal layout)

# Function for LAN - Utility Button
def on_sub_button():
    run_graph(1)  #set code_to_run to 1 (e.g., generate substation internal layout)

#WAN button
wanButton = tk.Button(
    text="WAN",
    width=13,
    height=1,
    bg="gray",
    fg="white",
    command=on_wan_button  #on_wan_button runs when clicked
)
wanButton.pack()
wanButton.place(x=10, y=50)

#LAN - Utility button
utilButton = tk.Button(
    text="LAN - Utility",
    width=13,
    height=1,
    bg="gray",
    fg="white",
    command=on_util_button  #on_util_button runs when clicked
)
utilButton.pack()
utilButton.place(x=130, y=50)

#LAN - Substation button
subButton = tk.Button(
    text="LAN - Substation",
    width=13,
    height=1,
    bg="gray",
    fg="white",
    command=on_sub_button  #on_sub_button runs when clicked
)
subButton.pack()
subButton.place(x=250, y=50)

root.mainloop()
