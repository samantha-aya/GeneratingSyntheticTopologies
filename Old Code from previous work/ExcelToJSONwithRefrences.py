# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import json
import xlrd

#sets the path for the excel file
excelFilePath = "/Users/sam.aya/Documents/Fall 2023/ECEN 689/new codes/SubstationCoordinates.xls"

outFilePath = "/Users/sam.aya/Documents/Fall 2023/ECEN 689/new codes/outputs"

#create excel object in python
excelFileObj = xlrd.open_workbook(excelFilePath)
#get the first sheet in excel file
firstSheet = excelFileObj.sheet_by_index(0)
#gets the number of rows in fist sheet
firstSheetLength = firstSheet.nrows


#Function is used to print a List to a file
# parameters: outputList = list of files to print to file, filePath = file path for file to be written to
def writeToFile(outputFile, outFilePath):
    modelFile = open(outFilePath+".json","w")
    modelFile.write(json.dumps(generalOutputs))
    modelFile.close()

# refernce Bus lists
refBusList = []

for i in range(1,firstSheetLength):
    singleBus = {
        "Bus Number": firstSheet.cell_value(i,1), 
        "Substation Number":firstSheet.cell_value(i,2),
        "Longitude":firstSheet.cell_value(i,3),
        "Latitude":firstSheet.cell_value(i,4)
        }
    refBusList.append(singleBus)



outputBusList = []
#get the second sheet in excel file
secondSheet = excelFileObj.sheet_by_index(1)
#gets the number of rows in second sheet
secondSheetLength = secondSheet.nrows

#sets the first 'From bus' in the excel sheet
currentBus = 0
newestBus = {}


for i in range(1,secondSheetLength):
    nextBus = secondSheet.cell_value(i,0)
    if currentBus != nextBus:
        currentBus = nextBus
         #search refBusArray for current Bus
        for x in range(0,len(refBusList)):
            checkBus = refBusList[x]
            #if bus found in refernce bus, add it to mcAllenBusList
            if checkBus["Bus Number"] == currentBus:
                newestBus = {
                        "Bus Number": checkBus["Bus Number"],
                        "Substation Number": checkBus["Substation Number"],
                        "Longitude": checkBus["Longitude"],
                        "Latitude": checkBus["Latitude"],
                        "Neighbors": []
                        }
                #add first To bus to neighbor of newestbus
                neighborBusNumber = secondSheet.cell_value(i,1)
                for potentialNeighborBus in refBusList:
                    if potentialNeighborBus["Bus Number"] == neighborBusNumber:
                        newestBus["Neighbors"].append(potentialNeighborBus)
                outputBusList.append(newestBus)
    else:
        #if fromBus has been added to mcAllenBusList alread, populate neighbors
        neighborBusNumber = secondSheet.cell_value(i,1)
        for potentialNeighborBus in refBusList:
            if potentialNeighborBus["Bus Number"] == neighborBusNumber:
                newestBus["Neighbors"].append(potentialNeighborBus)
print(outputBusList[0])
generalOutputs = {
        "outputBuses": outputBusList
        }

JSONstr = json.dumps(generalOutputs)
writeToFile(generalOutputs,"Excel to JSON Output")

##print(JSONstr)
