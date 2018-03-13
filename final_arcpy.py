"""
FANGNAN DU
FINAL PROJECT
This script is for developing a tool for the ambulance driver to find the optimal hospital and the best route.

To be specific, the script is just for the virginia beach. Because i did a project for the emergency call propbility in
virginia beach. So we will know where will the calls may happen. but after that, we need to know which hospital to go and what
is the best route for it. So in this final project, I want to finish the following part of the project, which is helping the
ambulance driver to find the optimal hospital and best route.

Data required:
-network dataset of virginia beach
-hospital dataset of virginia beach
-emergency calls dataset of virginia beach

To create an ArcToolbox tool with which to execute this script, do the following.
1   In  ArcMap > Catalog > Toolboxes > My Toolboxes, either select an existing toolbox
    or right-click on My Toolboxes and use New > Toolbox to create (then rename) a new one.
2   Drag (or use ArcToolbox > Add Toolbox to add) this toolbox to ArcToolbox.
3   Right-click on the toolbox in ArcToolbox, and use Add > Script to open a dialog box.
4   In this Add Script dialog box, use Label to name the tool being created, and press Next.
5   In a new dialog box, browse to the .py file to be invoked by this tool, and press Next.
6   In the next dialog box, specify the following inputs (using dropdown menus wherever possible)
    before pressing OK or Finish.
        DISPLAY NAME               DATA TYPE         PROPERTY>DIRECTION>VALUE
        Address Number             Long              Input(required)
        Street Orientation         String            Input(optional)
        Street Name                String            Input(required)
        Street type                String            Input(optional)
        EmergencyType              String            Input(required)
        Go to emergency            String            Input(optional)
        Go to hospital             String            Input(optional)
        Data Source                Folder            Input(required)
        Output                     workspace         Output(required)

"""




#Import necessary system modules
import arcpy
import sys, string, traceback
import os.path as op
try:
    #Set up the environment and allow the overwite
    arcpy.env.overwriteOutput = True
    #Check out the Network Analyst extension license
    arcpy.CheckOutExtension("Network")
    #--------------------------set the parameters--------------
    #Input Data source
    DataSource = arcpy.GetParameterAsText(0)
    #Before we run this model, we need to building the data set for the network Analyst
    NetworkDataset = DataSource + "\Street_ND.nd"     # network dataset
    Emergency = DataSource + "\Emergency.shp"     # Basic point layers of specific emergency Point
    Hospitals = DataSource + "\Hospitals.shp"      # Point layer for all hospital locations
    outGeodatabase = arcpy.GetParameterAsText(1)   # output workspace route
    # Emergency call Location
    NO = arcpy.GetParameterAsText(2)
    direct = arcpy.GetParameterAsText(3)
    street = arcpy.GetParameterAsText(4)
    type = arcpy.GetParameterAsText(5)
    # Hospital requirement
    EmergencyType = arcpy.GetParameterAsText(6)
    Ambulance = arcpy.GetParameterAsText(7)
    DriveTo = arcpy.GetParameterAsText(8)


    #--------------------emergency location create and hospital selection--------------
    arcpy.MakeFeatureLayer_management(Emergency, "lyr")   # Make a layer from the feature class
    # Incident address selection
    Start = NO+" "+direct+" "+street+" "+type
    Start = str(Start)
    #select point by location name
    arcpy.SelectLayerByAttribute_management("lyr", "NEW_SELECTION", '"Address" = ‘Start’')
    # copy the selecttion to a new point shapefile
    arcpy.CopyFeatures_management("lyr", "Incidents")
    Incidents = "Incidents"
    arcpy.AddMessage(‘Incident Address:’ + Start)

    # Hospital Selection
    # When the ambulance recieved the message, there will be a prioprity type, which indicates the hospital TYPE
    # if the priority is 1 ,then choose the highest level hospital
    if EmergencyType == "1":
        arcpy.Select_analysis(Hospitals, "HosSelection", '"CallPriority" = ‘1’')
    elif EmergencyType == "2":
        arcpy.Select_analysis(Hospitals, "HosSelection", '"CallPriority" = ‘2’')
    elif EmergencyType == "2":
        arcpy.Select_analysis(Hospitals, "HosSelection", '"CallPriority" = ‘3’')
    else:
        arcpy.CopyFeatures_management(Hospitals,"HosSelection")


    #--------------add the weighted impedance to select the best routed hospital before network analyse
    #calculate the distance from the hospital to emergency call
    arcpy.Near_analysis(Hospitals, Incidents)
    ## Add a weight field for impedance( the impedance is calculated by another script which showed at the end of the report)
    arcpy.AddField_management(Hospitals, "weight", "DOUBLE")
    # Calculate the distance based weigh of each selected hospital based on their median ranking
    arcpy.CalculateField_management(Hospitals, "weight", "( [median] / (Sqr ( [NEAR_DIST] ) ) ) * 100", "VB", "")
    # Determine the maximum wieghted ranking amongst the hospitals
    arcpy.Statistics_analysis(Hospitals, "Hos_max", "weight MAX", "")
    # Join the maximum wiegh back to the hospitals locations
    arcpy.JoinField_management(Hospitals, "weight", "Hos_max", "MAX_weight", "")
    # Select the hospitals locaiton with the highest weighted rank or equally 2 or more highest weighted rank
    Hospitals = arcpy.Select_analysis(Hospitals, "Hospitals", '"FREQUENCY" > 0')

    #----------after selected 1 or more equally weighted optimal hospitals, run the net work analyse to find the rount--------
    # Set up some constant
    # network analysis route layer
    outRoutes = "Routes"
    # network analysis direction data
    outDirections = "Directions"
    # network analysis selected hospital
    outClosestHospital = "ClosestHospital"
    # travel cost measure unit
    measurement_units = "Minutes"
    # travel from hospital to incident site
    Travel_Direction = "TRAVEL_FROM "

    #Direction Set
    Populate_Directions = "True"
    Directions_Language = "en"
    Directions_Distance_Units = "Mile"
    Directions_Style_Name = "NA Desktop"

    # Target point layers
    Incidents = "Incidents"
    Facilities = Hospitals
    Maximum_Facilities_to_Find = 1

    # Run FindClosestFacilities. Choose to find only the closest facility.

    arcpy.na.FindClosestFacilities( Incidents, Facilities, measurement_units, NetworkDataset, outGeodatabase, outRoutes,outDirections,outClosestHospital, Number_of_Facilities_to_Find=1)
    #-----------------------results DISPLAY---------------------------
    # Add the hospital, route and direction feature classes to a new dataframe
    currentMap = arcpy.mapping.MapDocument("CURRENT")
    currentDataFrame = currentMap.activeDataFrame
    layerToBeDisplayed1  = arcpy.mapping.Layer(outRoutes)
    arcpy.mapping.AddLayer(currentDataFrame, layerToBeDisplayed1,"TOP")
    layerToBeDisplayed2  = arcpy.mapping.Layer(outClosestHospital)
    arcpy.mapping.AddLayer(currentDataFrame, layerToBeDisplayed3,"TOP")

    del currentMap

    sequenceOfShapefileRecords = arcpy.SearchCursor(outClosestHospital)
    # Loop through that list, printing each field's type and name
    arcpy.AddMessage ( “ Optimal hospital is found.”)

    # Get the ID of finded hospital in order to find the specific info in orginal feature
    for nextRecord in sequenceOfShapefileRecords:
        ID = str(nextRecord.getValue(ORIG_FID))
    del sequenceOfShapefileRecords

    sequenceOfShapefileRecords = arcpy.SearchCursor(Facilities)
    # Print out hospital information
    for nextRecord in sequenceOfShapefileRecords:
          if str(nextRecord.getValue(FID)) == ID:
              arcpy.AddMessage (“Hospital Name:”+ str(nextRecord.getValue(Facilities))
              arcpy.AddMessage ("Hospital Address: " + str(nextRecord.getValue(Street))
    del sequenceOfShapefileRecords

    # Print out direction text
    Arcpy.AddMessage (“Route Direction:\n”)
    sequenceOfShapefileRecords = arcpy.SearchCursor(outDirections)
    for nextRecord in sequenceOfShapefileRecords:
        arcpy.AddMessage( str(nextRecord.getValue(Text)))

    # Travel distance & time
    del sequenceOfShapefileRecords
    sequenceOfShapefileRecords = arcpy.SearchCursor(outRoutes)
    for nextRecord in sequenceOfShapefileRecords:
        arcpy.AddMessage( “\n”+ str(nextRecord.getValue(Total_Minutes)))
        arcpy.AddMessage( str(nextRecord.getValue(Total_Miles)))

except Exception as e:
    # If unsuccessful, end gracefully by indicating why
    arcpy.AddError('\n' + "Script failed because: \t\t" + e.message )
    # ... and where
    exceptionreport = sys.exc_info()[2]
    fullermessage   = traceback.format_tb(exceptionreport)[0]
    arcpy.AddError("at this location: \n\n" + fullermessage + "\n")
