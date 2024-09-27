import tkinter as tk
from tkinter import ttk
import configparser  #for settings.ini file
import subprocess
import os
import shutil  #for deleting the old JSON files
import time  #to track the elapsed time
from threading import Thread  #to run the script asynchronously

#dictionary values for settings file based on GUI input
test_case_mapping = {
    'S. Carolina 500-bus': '500',
    'Texas 2,000-bus': '2k',
    'WECC 10,000-bus': '10k'
}

running = False  #global flag to check if the script is running


#function to clear the output folders
def clear_output_directories():
    directories_to_clear = [
        "Output\\Substations",
        "Output\\Utilities",
        "Output\\Regulatory"
    ]

    for directory in directories_to_clear:
        if os.path.exists(directory):
            #clear the directory by old JSONs
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  #remove the file
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  #remove the directory and its contents
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')


#function to update the existing INI settings file and run the second script
def save_settings_and_run():
    #start a new thread for running the script and timing
    def run_script():
        global running  #set the flag to True when the script starts
        running = True

        #delay for 2 seconds before starting the timer
        time.sleep(2)

        start_time = time.time()

        #show the timer label at the bottom after the script starts running
        timer_label.place(x=10, y=240)  #adjust the label location (y=240)
        update_timer(start_time)  #start updating the timer

        config = configparser.ConfigParser()

        #load the existing INI settings file
        config.read("settings.ini")

        #get the selected test case and map it to the desired value
        selected_test_case = testCasevar.get()
        mapped_test_case = test_case_mapping.get(selected_test_case, 'default_case')

        #update the settings with the new values from the GUI
        config['DEFAULT']['n_clusters'] = str(int(uccNumber.get()))
        config['DEFAULT']['n_ba'] = str(int(baNumber.get()))
        config['DEFAULT']['case'] = f"'{mapped_test_case}'"  #save the mapped test case value in quotes

        #update topology and no_powerworld based on selection
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

        #save the updated settings back to the INI file
        with open("settings.ini", "w") as configfile:
            config.write(configfile)

        #clear the output directories before running the next script
        clear_output_directories()

        #run the next script using subprocess
        subprocess.run(["C:/GitHubProjects/ECEN689Project/venv1/Scripts/python", "ObjectOrientedJSONGen.py"])
        #subprocess.run(["ECEN689Project//venv1//Scripts//python", "ObjectOrientedJSONGen.py"]) ???

        end_time = time.time()
        elapsed_time = end_time - start_time
        update_timer_label(elapsed_time)  #stop the timer and show final time including milliseconds (for analysis purposes)

        running = False  #set the flag to False when the script finishes

    #run the script in a separate thread
    script_thread = Thread(target=run_script)
    script_thread.start()


#function to update the timer every 10 milliseconds (without milliseconds in the display bc it's too much visually)
def update_timer(start_time):
    if running:  #keep updating the timer while the script is running
        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds = int(remainder)

        timer_label.config(
            text=f"Generating JSON files, time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")

        #schedule the next update in 10 milliseconds
        root.after(10, lambda: update_timer(start_time))


#function to stop the timer and display the final elapsed time including milliseconds
def update_timer_label(elapsed_time):
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds, milliseconds = divmod(remainder, 1)

    #display completed time including milliseconds at the end
    timer_label.config(
        text=f"Completed! Total time: {int(hours):02}:{int(minutes):02}:{int(seconds):02}.{int(milliseconds * 1000):03}")

    #wait for a few seconds before running visualizationSelection.py
    root.after(2000, run_visualization)  #wait for 3000 milliseconds (3 seconds)


def run_visualization():
    subprocess.run(["C:/GitHubProjects/ECEN689Project/venv1/Scripts/python", "visualizationSelection.py"])


#GUI code
root = tk.Tk()
root.geometry('220x275')  #set the size of the window

#title
configTitle = tk.Label(text="Configuration Window")
configTitle.pack()
configTitle.place(x=50, y=0)

#label for test case selection
caseSelection = tk.Label(text="Case:")
caseSelection.pack()
caseSelection.place(x=10, y=30)

#combobox for test case selection
testCasevar = tk.StringVar()
testCase = ttk.Combobox(root, textvariable=testCasevar)
testCase['values'] = ('S. Carolina 500-bus', 'Texas 2,000-bus', 'WECC 10,000-bus')
testCase.state(["readonly"])
testCase.pack()
testCase.place(x=50, y=30)

#label for topology selection
topology = tk.Label(text="Topology:")
topology.pack()
topology.place(x=10, y=60)

#radio buttons for topologies
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

#label & spinbox for the UCC's
numUCC = tk.Label(text="Number of UCC's:")
numUCC.pack(side=tk.LEFT)
numUCC.place(x=10, y=130)
uccNumber = tk.DoubleVar()
uccSpinbox = tk.Spinbox(root, from_=1, to=100, increment=1, textvariable=uccNumber, width=4)
uccSpinbox.place(x=120, y=130)

#label & spinbox for the BA's
numBA = tk.Label(text="Number of BA's:")
numBA.pack(side=tk.LEFT)
numBA.place(x=10, y=150)
baNumber = tk.DoubleVar()
baSpinbox = tk.Spinbox(root, from_=1, to=50, increment=1, textvariable=baNumber, width=4)
baSpinbox.place(x=120, y=150)

#create the timer label but keep it hidden
timer_label = tk.Label(root, text="Loading... Elapsed time: 00:00:00")
timer_label.pack_forget()  #hide the label initially

#bind the "Run" button to save settings and run the script
runButton = tk.Button(
    root,
    text="Run",
    width=3,
    height=1,
    bg="gray",
    fg="white",
    command=save_settings_and_run  #bind the function here
)
runButton.pack()
runButton.place(x=90, y=200)

root.mainloop()
