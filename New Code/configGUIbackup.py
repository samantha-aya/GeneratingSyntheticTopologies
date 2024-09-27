import tkinter as tk
from tkinter import ttk
import configparser  # For working with INI files
import subprocess
import os
import shutil  # For deleting files and directories
import time  # To track the elapsed time
from threading import Thread  # To run the script asynchronously

# Dictionary mapping the test case names to their corresponding values
test_case_mapping = {
    'S. Carolina 500-bus': '500',
    'Texas 2,000-bus': '2k',
    'WECC 10,000-bus': '10k'
}

running = False  # Global flag to check if the script is running


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
    # Start a new thread for running the script and timing
    def run_script():
        global running  # Set the flag to True when the script starts
        running = True

        # Delay for 2 seconds before starting the timer
        time.sleep(2)

        start_time = time.time()

        # Show the timer label at the bottom after the script starts running
        timer_label.place(x=10, y=240)  # Adjust the label slightly lower (y=240)
        update_timer(start_time)  # Start updating the timer

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
        subprocess.run(["C:/GitHubProjects/ECEN689Project/venv1/Scripts/python", "ObjectOrientedJSONGen.py"])

        end_time = time.time()
        elapsed_time = end_time - start_time
        update_timer_label(elapsed_time)  # Stop the timer and show final time with milliseconds

        running = False  # Set the flag to False when the script finishes

    # Run the script in a separate thread
    script_thread = Thread(target=run_script)
    script_thread.start()


# Function to update the timer every 10 milliseconds (without milliseconds in the display)
def update_timer(start_time):
    if running:  # Keep updating the timer while the script is running
        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds = int(remainder)

        timer_label.config(
            #text=f"Loading... Elapsed time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
            text = f"Generating JSON files, time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")

        # Schedule the next update in 10 milliseconds
        root.after(10, lambda: update_timer(start_time))


# Function to stop the timer and display the final elapsed time including milliseconds
def update_timer_label(elapsed_time):
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds, milliseconds = divmod(remainder, 1)

    # Display completed time including milliseconds at the end
    timer_label.config(
        text=f"Completed! Total time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(milliseconds * 1000):03}")


# GUI Code
root = tk.Tk()
root.geometry('220x275')  # Set the size of the window

configTitle = tk.Label(text="Configuration Window")
configTitle.pack()
configTitle.place(x=50, y=0)

caseSelection = tk.Label(text="Case:")
caseSelection.pack()
caseSelection.place(x=10, y=30)

testCasevar = tk.StringVar()
testCase = ttk.Combobox(root, textvariable=testCasevar)
testCase['values'] = ('S. Carolina 500-bus', 'Texas 2,000-bus', 'WECC 10,000-bus')
testCase.state(["readonly"])
testCase.pack()
testCase.place(x=50, y=30)

topology = tk.Label(text="Topology:")
topology.pack()
topology.place(x=10, y=60)

topologySelection = tk.StringVar()
star = ttk.Radiobutton(root, text='Star', variable=topologySelection, value='star')
radial = ttk.Radiobutton(root, text='Radial', variable=topologySelection, value='radial')
statistics = ttk.Radiobutton(root, text='Statistics-Based', variable=topologySelection, value='statistics')
star.pack(anchor='w')
radial.pack(anchor='w')
statistics.pack(anchor='w')
star.place(x=70, y=60)
radial.place(x=70, y=80)
statistics.place(x=70, y=100)

numUCC = tk.Label(text="Number of UCC's:")
numUCC.pack(side=tk.LEFT)
numUCC.place(x=10, y=130)
uccNumber = tk.DoubleVar()
uccSpinbox = tk.Spinbox(root, from_=1, to=100, increment=1, textvariable=uccNumber, width=4)
uccSpinbox.place(x=120, y=130)

numBA = tk.Label(text="Number of BA's:")
numBA.pack(side=tk.LEFT)
numBA.place(x=10, y=150)
baNumber = tk.DoubleVar()
baSpinbox = tk.Spinbox(root, from_=1, to=50, increment=1, textvariable=baNumber, width=4)
baSpinbox.place(x=120, y=150)

# Create the timer label but keep it hidden initially
timer_label = tk.Label(root, text="Loading... Elapsed time: 00:00:00")
timer_label.pack_forget()  # Hide the label initially

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
runButton.place(x=90, y=200)

root.mainloop()
