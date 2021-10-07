# Units
* Be aware that the input time and frequency of the frame are in the unit of BU.
* The index i is for the frequency domain and j is for the time domain.
* Better set the time domain of the eframe and gframe with the same time length.
* The request data rate of each UE is in bit per frame, <br>
  e.g. if frame = 1ms and the request data rate is 3Mbps. <br>
       The input request data rate will be 3_000_000/1000. <br>
       If frame = 10ms, the input will be 3_000_000/100. <br>



# Simulation
## Generate Data
Run: "main_gen_XXX.py" <br>
Input: Parameters <br>
Output: JSON files. The parameters for the input of algorithms [Saved to "src/simulation/data"] <br>
* Setting parameters: <br>
    Most of the parameters settings are in the Python files "main_gen_data_XXX.py" <br>
    Except the range of MCS is in "src/resource_allocation/ds/util_enum.py" get_worst() and get_best()

## Run Simulation and Generate Chart
Input: <br>
(1) Folder name of the generated data in "src/simulation/data" <br>
(2) Folder name of the MCS range. Better be the same as the settings in "src/resource_allocation/ds/util_enum.py" <br>
(3) Iteration. Must be smaller or equal to the generated data in "src/simulation/data/FolderNameOfTheGeneratedData" <br>
Output: [Saved to "src/simulation/graph"] <br>
(1) JSON files of every iteration with algorithms in separate files <br>
(2) PDF and JSON files of charts <br>
* Uncomment the "IterateAlgo()" to run the simulation
* Uncomment the "GraphGenerator()" to draw the charts
* If one of the iterations of an algorithm failed to fully output the JSON file, run "main_single_run.py".



# Run Single Algorithm
* "main.py" is my algorithm
* "main_mcuphm.py" is "Multi-Connectivity Enabled User Association"
* "main_frsa.py" is "Resource Allocation in 5G with NOMA-Based Mixed Numerology Systems"
* "main_msema.py" is "Joint Resource Block-Power Allocation for NOMA-Enabled Fog Radio Access Networks"



# Draw Chart
Run "src/simulation/graph/util_graph.py" to draw a chart of a simulation



# Install
1. Install PyCharm
2. Configure a Pipenv environment