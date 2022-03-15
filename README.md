# BDFL-Simulation
 Simulation of the BDFL Fantasy League Season

# Directory
/data
    - contains the data files used for PFF projections and past defensive performances by team
    
/outputs
    - any output files written by the program are stored here
    
/src
    - this directory holds the source code
    API_Wrapper.py - formats calls to the MFL API
    Reporter.py - combines and organizes calls to API_Wrapper.py to produce relevant outputs
    Data_Generator.py - reads expert rankings and depth chart corrleations to generate random player performances for each game
    Simulator.py - Executes the BDFL schedule calculating wins and losses
    
Explation of the approach is available [here](https://nbviewer.org/github/PatrickBrayPersonal/BDFL-Simulation/blob/main/src/Report.ipynb)
