import tkinter as tk
from tkinter import ttk
import configparser  # For working with INI files
import subprocess
import os
import shutil  # For deleting files and directories

# Dictionary mapping the test case names to their corresponding values
test_case_mapping = {
    'S. Carolina 500-bus': '500',
    'Texas 2,000-bus': '2k',
    'WECC 10,000-bus': '10k'
}

# Function to clear the contents of the output directories
def clear_output_directories():
    directories_to_clear = [
        "Output\\Substations",
        "Output\\Utilities",
        "Output\\Regulatory"
    ]

    for directory in directories_to_clear:
        if os.path.exists(directory):
            # Clear the directory by removing its contents
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Remove the file or symbolic link
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove the directory and its contents
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')

# Function to update the existing INI settings file and run the second script
def save_settings_and_run():
    config = configparser.ConfigParser()

    # Load the existing INI settings file
    config.read("settings.ini")

    # Get the selected test case and map it to the desired value
    selected_test_case = testCasevar.get()
    mapped_test_case = test_case_mapping.get(selected_test_case, 'default_case')

    # Update the settings with the new values from the GUI
    config['DEFAULT']['n_clusters'] = str(int(uccNumber.get()))  # No quotes for n_clusters
    config['DEFAULT']['n_ba'] = str(int(baNumber.get()))  # No quotes for n_ba
    config['DEFAULT']['case'] = f"'{mapped_test_case}'"  # Save the mapped test case value in quotes

    # Update topology and no_powerworld based on selection
    selected_topology = topologySelection.get()
    if selected_topology == 'star':
        config['DEFAULT']['topology_configuration'] = "'star'"
        config['DEFAULT']['no_powerworld'] = "'True'"
    elif selected_topology == 'radial':
        config['DEFAULT']['topology_configuration'] = "'radial'"
        config['DEFAULT']['no_powerworld'] = "'True'"
    elif selected_topology == 'statistics':
        config['DEFAULT']['topology_configuration'] = "'statistics'"
        config['DEFAULT']['no_powerworld'] = "'False'"

    # Save the updated settings back to the INI file
    with open("settings.ini", "w") as configfile:
        config.write(configfile)

    # Clear the output directories before running the next script
    clear_output_directories()

    # Run the next script using subprocess
    subprocess.run(["python", "ObjectOrientedJSONGen.py"])

# GUI Code
root = tk.Tk()
root.geometry('200x250')  # Set the size of the window

configTitle = tk.Label(text="Configuration Window")
configTitle.pack()
configTitle.place(x=40, y=0)

caseSelection = tk.Label(text="Case:")
caseSelection.pack()
caseSelection.place(x=0, y=30)

testCasevar = tk.StringVar()
testCase = ttk.Combobox(root, textvariable=testCasevar)
testCase['values'] = ('S. Carolina 500-bus', 'Texas 2,000-bus', 'WECC 10,000-bus')
testCase.state(["readonly"])
testCase.pack()
testCase.place(x=40, y=30)

topology = tk.Label(text="Topology:")
topology.pack()
topology.place(x=0, y=60)

topologySelection = tk.StringVar()
star = ttk.Radiobutton(root, text='Star', variable=topologySelection, value='star')
radial = ttk.Radiobutton(root, text='Radial', variable=topologySelection, value='radial')
statistics = ttk.Radiobutton(root, text='Statistics-Based', variable=topologySelection, value='statistics')
star.pack(anchor='w')
radial.pack(anchor='w')
statistics.pack(anchor='w')
star.place(x=60, y=60)
radial.place(x=60, y=80)
statistics.place(x=60, y=100)

numUCC = tk.Label(text="Number of UCC's:")
numUCC.pack(side=tk.LEFT)
numUCC.place(x=0, y=130)
uccNumber = tk.DoubleVar()
uccSpinbox = tk.Spinbox(root, from_=1, to=100, increment=1, textvariable=uccNumber, width=4)
uccSpinbox.place(x=110, y=130)

numBA = tk.Label(text="Number of BA's:")
numBA.pack(side=tk.LEFT)
numBA.place(x=0, y=150)
baNumber = tk.DoubleVar()
baSpinbox = tk.Spinbox(root, from_=1, to=50, increment=1, textvariable=baNumber, width=4)
baSpinbox.place(x=110, y=150)

# Bind the "Run" button to save settings and run the script
runButton = tk.Button(
    root,
    text="Run",
    width=3,
    height=1,
    bg="gray",
    fg="white",
    command=save_settings_and_run  # Bind the function here
)
runButton.pack()
runButton.place(x=80, y=200)

root.mainloop()
