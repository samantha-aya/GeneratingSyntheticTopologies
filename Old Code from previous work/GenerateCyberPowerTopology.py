from utility_model import *
import os
import pandas as pd

cwd = os.getcwd()

#get input substation data from excel
substation_data = pd.read_excel(os.path.join(cwd, '../Input\\', '37BusCaseSubstations.xlsx'))

#Convert DataFrame to dictionary with substation number as key and lat,lon as values
location_dict = substation_data.set_index('Sub Num')[['Latitude', 'Longitude']].T.apply(tuple).to_dict()

#Calling functions from utility_model.py
substationNumbers = substation_data['Sub Num'].tolist()
utilityNumber = [2]
generateSubstationLevel(substationNumbers,utilityNumber)
generateUtilityLevel(substationNumbers, utilityNumber)
generateRegulatoryLevel(utilityNumber)