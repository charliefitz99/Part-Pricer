import tkinter as tk
from tkinter import messagebox
import string
import pymssql


f = open("userpass.txt","r")
contents = f.read().splitlines()
#Epicor Connection
conn = pymssql.connect(server=contents[0],port=1433, user=contents[1], password=contents[2], database="epicor10")
cursor = conn.cursor()
#Query Start Date
startDate = '2019-01-01'

#Starts SQL query and sets up display
def getData():    
    print(" ")
    print("-------------------------")
    partNumber = partEntryUI.get()
    print("Part Number: " + partNumber)
    marginString = desiredMarginUI.get()
    if marginString == "":
        margin = 30
    else:
        margin = float(marginString)
    sqlQuery(partNumber)
    
    #Configure output
    #Header
    stdLabel.configure(fg = "black")
    actLabel.configure(fg = "black")
    
    #Column 0
    salesPriceUnitLabel.configure(fg = "black")
    totalCostUnitLabel.configure(fg = "black")
    gmUnitLabel.configure(fg = "black")
    salesPriceExtLabel.configure(fg = "black")
    totalCostExtLabel.configure(fg = "black")
    gmExtLabel.configure(fg = "black")
    gmPercentLabel.configure(fg = "black")
    
    #Column 1
    salesPriceUnitStdUI.configure(text = round(currentPrice,2))
    totalCostUnitStdUI.configure(text = round(stdUnit,2))
    gmUnitStdColor = "red" if (currentPrice - stdUnit) < 0 else "black"
    gmUnitStdUI.configure(text = round(currentPrice - stdUnit,2), fg =  gmUnitStdColor)
    salesPriceExtStdUI.configure(text = round(currentPrice*totalShipped,2))
    totalCostExtStdUI.configure(text = round(stdUnit*totalShipped,2))
    gmExtStdColor = "red" if ((currentPrice*totalShipped)-(stdUnit*totalShipped)) < 0 else "black"
    gmExtStdUI.configure(text = round((currentPrice*totalShipped)-(stdUnit*totalShipped), 2), fg = gmExtStdColor)
    gmPercentStd = (((currentPrice*totalShipped)-(stdUnit*totalShipped))/(stdUnit*totalShipped))*100
    gmPercentStdUI.configure(text = str(round(gmPercentStd, 2)) + "%",fg = gmExtStdColor)
    
    #Column 3
    salesPriceUnitActUI.configure(text = round(currentPrice,2))
    totalCostUnitActUI.configure(text = str(round(avgUnitCost, 2)))
    gmUnitActColor = "red" if (currentPrice - avgUnitCost) < 0 else "black"
    gmUnitActUI.configure(text = round(currentPrice - avgUnitCost, 2), fg = gmUnitActColor)
    salesPriceExtActUI.configure(text = round(currentPrice*totalShipped,2))
    totalCostExtActUI.configure(text = round(shipCost,2))
    gmExtActColor = "red" if ((currentPrice*totalShipped)-(avgUnitCost*totalShipped)) < 0 else "black"
    gmExtActUI.configure(text = round((currentPrice*totalShipped)-(avgUnitCost*totalShipped),2), fg = gmExtActColor)
    gmPercentAct = (((currentPrice*totalShipped)-(avgUnitCost*totalShipped))/(avgUnitCost*totalShipped))*100
    gmPercentActUI.configure(text = str(round(gmPercentAct, 2)) + "%", fg = gmExtActColor)
    
    #Column 5
    customerLabel.configure(fg = "black")
    numJobsLabel.configure(fg = "black")
    avgLotLabel.configure(fg = "black")
    stdAccLabel.configure(fg = "black")
    stdUpdateLabel.configure(fg = "black")
    lastShipLabel.configure(fg = "black")
    quoteNumLabel.configure(fg = "black")
    lastQuoteDateLabel.configure(fg = "black")
    cellCodeLabel.configure(fg = "black")
    
    #Column 6
    customerUI.configure(text = customer)
    numJobsUI.configure(text = len(jobs))
    avgLotUI.configure(text = round(getAvgLotSize(),2))
    stdAccuracy = getStdAcc()
    stdAccColor = "red" if stdAccuracy > .25 or stdAccuracy < -.25 else "green"
    stdAccUI.configure(text = str(abs(round(stdAccuracy*100, 2))) + "%", fg = stdAccColor)
    stdUpdateUI.configure(text = lastStdUpdate)
    lastShipUI.configure(text = lastShipDate)
    quoteNumUI.configure(text = quoteNumber)
    lastQuoteDateUI.configure(text = lastQuoteDate)
    cellCodeUI.configure(text = cellCode)
    
    #Column 8
    laborBurdenLabel.configure(fg = "black")
    opLabel.configure(fg = "black")
    materialLabel.configure(fg = "black")
    
    #Column 9
    laborBurdenUI.configure(text = str(round(getPercentLaborBurden()*100, 2)) + "%")
    opUI.configure(text = str(round(getPercentOP()*100, 2)) + "%")
    materialUI.configure(text = str(round(getPercentMaterial()*100,2)) + "%")
    
    
    #Clear suggested price numbers before writing new ones
    tk.Label(masterUI, text = "                             ").place(x = 192, y = 985)
    actSuggestPriceUI = tk.Label(masterUI, text = str(round(getSuggestActPrice(margin),2))).place(x = 192 , y = 985)
    tk.Label(masterUI, text = "                              ").place(x = 192, y = 965)
    stdSuggestPriceUI = tk.Label(masterUI, text = str(round(getSuggestStdPrice(margin),2))).place(x = 192 , y = 965)        
    
#Performs queries and sets global variables for rest of program to utilize
def sqlQuery(partNumber):
    #ANALYSIS STARTDATE
    global startDate
    
    #Global variables
    global currentPrice
    global extGM
    global stdUnit
    global lastStdUpdate
    global totalQty
    global totalShipped
    global totalCost
    global totalLabor
    global totalBurden
    global totalMaterial
    global totalOP
    global totalRevenue
    global customer
    global lastShipDate
    global numJobs
    global totalIssued
    global actCompleted
    global avgUnitCost
    global quoteNumber
    global lastQuoteDate
    global shipCost
    global cellCode
    
    #Global Arrays
    global jobs
    global jobQtys
    global laborExtCosts
    global burdenExtCosts
    global materialExtCosts
    global opExtCosts
    global shipQtys
    global totalShipped
    global issueDates
    global completeDates
    issueDates = []
    completeDates = []
    jobs = []
    jobQtys = []
    laborExtCosts = []
    burdenExtCosts = []
    materialExtCosts = []
    opExtCosts = []
    shipQtys = []
    issueQtys = []
    actComplete = []
    
    #Get Price
    cursor.execute("SELECT UnitPrice FROM Erp.InvcDtl WHERE partNum = '{}' AND ShipDate >= '{}' ORDER BY ShipDate".format(partNumber,startDate))
    pricePoints = cursorTranslateFloat(cursor.fetchall())
    for row in pricePoints: 
        currentPrice = row
    
    #Get Jobs by date
    cursor.execute("SELECT JobNum FROM Erp.JobHead WHERE PartNum = '{}' AND WIStartDate >= '{}' AND ClosedDate <= GETDATE() ORDER BY WIStartDate".format(partNumber,startDate))
    jobs = cursorTranslate(cursor.fetchall())
    if len(jobs) == 0:
        messagebox.showerror("Error", "No Jobs Found")
        # tk.messagebox(no jobs found)
    
    #Get ship quantities by date from ship detail
    cursor.execute("SELECT OurInventoryShipQty FROM Erp.shipdtl WHERE PartNum = '{}' AND ChangeDate >= '{}'".format(partNumber,startDate)) 
    shipQtys = cursorTranslateFloat(cursor.fetchall())
    totalShipped = 0
    for shipDtl in shipQtys:
        totalShipped = totalShipped + shipDtl
    
    # Get Job Quantities by date
    for job in jobs:
        #Get Job dates
        cursor.execute("SELECT WIStartDate from erp.jobhead where jobNum = '%s'" %(job))
        issueDates.append(cursorTranslateSingle(cursor.fetchall()))
        cursor.execute("SELECT ClosedDate from erp.jobhead where jobNum = '%s'" %(job))
        completeDates.append(cursorTranslateSingle(cursor.fetchall()))
        #Get issued quantities
        cursor.execute("SELECT ProdQty from erp.jobhead where JobNum = '%s'" %(job))
        issueQtys.append(cursorTranslateFloatSingle(cursor.fetchall()))
        cursor.execute("SELECT QtyCompleted from erp.jobhead where JobNum = '%s'" %(job)) 
        actComplete.append(cursorTranslateFloatSingle(cursor.fetchall()))
        #actual qtys
        cursor.execute("SELECT QtyCompleted from erp.jobhead where JobNum = '%s'" %(job))
        # if cursorTranslateFloatSingle(cursor.fetchall()) <= 0:
            # cursor.execute("SELECT ProdQty from erp.jobhead where JobNum = '%s'" %(job))
        # else:
            # cursor.execute("SELECT QtyCompleted from erp.jobhead where JobNum = '%s'" %(job))    
        jobQtys.append(cursorTranslateFloatSingle(cursor.fetchall()))
        #Get extended labor costs for job by date
        cursor.execute("SELECT TLALaborCost from Erp.JobAsmbl where JobNum = '%s'" %(job))
        laborExtCosts.append(cursorTranslateFloatSingle(cursor.fetchall()))
        #Get extended material costs for job by date
        cursor.execute("SELECT TLAMaterialCost from Erp.JobAsmbl where JobNum = '%s'" %(job))
        materialExtCosts.append(cursorTranslateFloatSingle(cursor.fetchall()))
        #Get extended op costs for job by date
        cursor.execute("SELECT TLASubContractCost from Erp.JobAsmbl where JobNum = '%s'" %(job))
        opExtCosts.append(cursorTranslateFloatSingle(cursor.fetchall()))
    
    #Get extended burden costs for job by date   
    for cost in laborExtCosts:
        burdenExtCosts.append(cost*2.3)
    
    #Get standard
    cursor.execute("SELECT StdLaborCost FROM erp.partcost WHERE PartNum = '%s'" %(partNumber))
    stdLabor = cursorTranslateFloatSingle(cursor.fetchall())
    cursor.execute("SELECT StdBurdenCost FROM erp.partcost WHERE PartNum = '%s'" %(partNumber))
    stdBurden = cursorTranslateFloatSingle(cursor.fetchall())
    cursor.execute("SELECT StdMaterialCost FROM erp.partcost WHERE PartNum = '%s'" %(partNumber))
    stdMaterial = cursorTranslateFloatSingle(cursor.fetchall())
    cursor.execute("SELECT StdSubContCost FROM erp.partcost WHERE PartNum = '%s'" %(partNumber))
    stdOP = cursorTranslateFloatSingle(cursor.fetchall())
    stdUnit = (stdLabor + stdBurden + stdMaterial + stdOP)
    
    #Get Last Standard update:
    cursor.execute("SELECT sysdate FROM Erp.parttran where partNum = '%s' and TranType = 'ADJ-CST' order by sysdate" %(partNumber))
    tranHist = cursorTranslate(cursor.fetchall())
    for tran in tranHist:
        lastStdUpdate = tran
    
    #Get lastShipDate
    cursor.execute("SELECT ChangeDate FROM Erp.shipdtl WHERE PartNum = '{}' AND ChangeDate >= '{}' ORDER BY changeDate".format(partNumber,startDate))
    shipDates = cursorTranslate(cursor.fetchall())
    for date in shipDates:
        lastShipDate = date
        
    #Get extended figures
    totalQty = 0
    totalLabor = 0
    totalBurden = 0
    totalMaterial = 0
    totalOP = 0
    totalIssued = 0
    actCompleted = 0
    for i in range(len(jobs)):
        totalLabor = totalLabor + laborExtCosts[i]
        totalBurden = totalBurden + burdenExtCosts[i]
        totalMaterial = totalMaterial + materialExtCosts[i]
        totalOP = totalOP + opExtCosts[i]
        totalQty = totalQty + jobQtys[i]
        totalIssued = totalIssued + issueQtys[i]
        actCompleted = actCompleted + actComplete[i]
        print(" ")
        print("Job: " + jobs[i])
        print("Issue Date: " + issueDates[i])
        print("Completion Date: " + completeDates[i])
        print("Labor Unit: " + str(round(laborExtCosts[i]/jobQtys[i],2)))
        print("Burden Unit: " + str(round(burdenExtCosts[i]/jobQtys[i],2)))
        print("Material Unit: " + str(round(materialExtCosts[i]/jobQtys[i],2)))
        print("OP Unit: " + str(round(opExtCosts[i]/jobQtys[i],2)))
    totalCost = totalLabor + totalBurden + totalMaterial + totalOP
    avgUnitCost = totalCost/totalQty
    shipCost = avgUnitCost*totalShipped
    totalRevenue = currentPrice*totalShipped
    extGM = totalRevenue-shipCost
    numJobs = len(jobs)
    
    #Get Customer
    cursor.execute("select prodcode from erp.part where partnum = '%s'" %(partNumber))
    customerIDs = cursorTranslate(cursor.fetchall())
    for row in customerIDs:
        customerID = row
    cursor.execute("select description from erp.prodgrup where prodcode = '%s'" %(customerID))
    customers = cursorTranslate(cursor.fetchall())
    for row in customers:
        customer = row
        
    #Get Quote/quoteDate
    cursor.execute("SELECT QuoteNum FROM erp.quotedtl WHERE PartNum = '%s' ORDER BY lastUpdate" %(partNumber))
    quoteNumbers = cursorTranslate(cursor.fetchall())
    quoteNumber = None
    for quote in quoteNumbers:
        quoteNumber = quote
    if(quoteNumber == None):
        quoteNumber = "Not Found"
    if(quoteNumber != "Not Found"):
        cursor.execute("SELECT LastUpdate FROM erp.quoteDtl WHERE QuoteNum = '%s'" %(quoteNumber))
        lastQuoteDate = cursorTranslateSingle(cursor.fetchall())
    else:
        lastQuoteDate = "N/A"
        
    #Get CellCode
    cursor.execute("SELECT userChar2 from erp.part where partNum = '%s'" %(partNumber))
    cellCode = cursorTranslateSingle(cursor.fetchall())
    
#Returns standard accuracy coefficient (1-(actualTotalCost/stdTotalCost))
def getStdAcc():
    totalStandardCost = stdUnit*totalQty
    return (1-(totalStandardCost/totalCost))

#Returns average lot size
def getAvgLotSize():
    return totalQty/numJobs

#Returns percentage of cost devoted to labor
def getPercentLaborBurden():
    return ((totalBurden + totalLabor)/totalCost)
    
# Returns percentage of total cost devoted to material
def getPercentMaterial():
    return (totalMaterial/totalCost)

# Returns percentage of total cost devoted to OP
def getPercentOP():
    return (totalOP/totalCost)

#Translate SQL query into string array 
def cursorTranslate(cursorOutput):
    #result array
    outputs = []
    #parse through outputs and extract non number characters
    for row in cursorOutput:
        row = str(row)
        row = row.replace('(','')
        row = row.replace('D','')
        row = row.replace('e','')
        row = row.replace('c','')
        row = row.replace('i','')
        row = row.replace('m','')
        row = row.replace('a','')
        row = row.replace('l','')
        row = row.replace(')','')
        row = row.replace(',','')
        row = row.replace("'",'')
        outputs.append(row)
    return outputs
    
#Translate SQL query into string
def cursorTranslateSingle(cursorOutput):
    #result array
    output = None
    #parse through outputs and extract non number characters
    for row in cursorOutput:
        row = str(row)
        row = row.replace('(','')
        row = row.replace('D','')
        row = row.replace('e','')
        row = row.replace('c','')
        row = row.replace('i','')
        row = row.replace('m','')
        row = row.replace('a','')
        row = row.replace('l','')
        row = row.replace(')','')
        row = row.replace(',','')
        row = row.replace("'",'')
        output = row
    return output

#Translate SQL query into float array 
def cursorTranslateFloat(cursorOutput):
    #result array
    outputs = []
    #parse through outputs and extract non number characters
    for row in cursorOutput:
        row = str(row)
        row = row.replace('(','')
        row = row.replace('D','')
        row = row.replace('e','')
        row = row.replace('c','')
        row = row.replace('i','')
        row = row.replace('m','')
        row = row.replace('a','')
        row = row.replace('l','')
        row = row.replace(')','')
        row = row.replace(',','')
        row = row.replace("'",'')
        row = float(row)
        outputs.append(row)
    return outputs

#Translate SQL query with a single entry to float variable
def cursorTranslateFloatSingle(cursorOutput):
    #result array
    output = 0
    #parse through outputs and extract non number characters
    for row in cursorOutput:
        row = str(row)
        row = row.replace('(','')
        row = row.replace('D','')
        row = row.replace('e','')
        row = row.replace('c','')
        row = row.replace('i','')
        row = row.replace('m','')
        row = row.replace('a','')
        row = row.replace('l','')
        row = row.replace(')','')
        row = row.replace(',','')
        row = row.replace("'",'')
        row = float(row)
        output = row
    return output

#Get percentage scrapLabel
def getPercentScrap():
    print(totalIssued)
    print(actCompleted)
    return (totalIssued-actCompleted)/totalIssued

#Suggest Price based on actuals
def getSuggestActPrice(margin):
    margin = (margin + 100)/100
    return margin*avgUnitCost
    
#Suggest Price based on standard
def getSuggestStdPrice(margin):
    margin = (margin + 100)/100
    return margin*stdUnit

#UI Setup
masterUI = tk.Tk()
masterUI.geometry("1920x1080")

#Data Window/display/border
windowBorderUI = tk.Frame(masterUI)
windowBorderUI.place(x=23,y=58)
windowBorderUI.configure(height = 904, width = 1864, bg = "black")
dataDisplayUI = tk.Frame(masterUI)
dataDisplayUI.place(x = 25, y = 60)
dataDisplayUI.configure(height = 900, width = 1860, bg = "white")
dataWindowUI = tk.Frame(masterUI)
dataWindowUI.place(x = 25, y = 60)
dataWindowUI.configure(height = 900, width = 1860, bg = "white")


#Data Window Contents

#Standards Vs Act Area
################################################

#Window Column 0
#Row 0
tk.Label(dataWindowUI, text = " ", bg = "white").grid(row = 0, column = 0)
#Row 10
salesPriceUnitLabel = tk.Label(dataWindowUI,text = "Sales Price Unit: ",bg = "white",fg =  "white")
salesPriceUnitLabel.grid(row = 1, column = 0,sticky = tk.E)
#Row 2
totalCostUnitLabel = tk.Label(dataWindowUI, text = "Total Cost Unit: ", bg = "white", fg =  "white")
totalCostUnitLabel.grid(row = 2, column = 0, sticky = tk.E)
#Row 3
gmUnitLabel = tk.Label(dataWindowUI, text = "GM Unit: ", bg = "white", fg =  "white")
gmUnitLabel.grid(row = 3, column = 0, sticky = tk.E)
#Row 4
tk.Label(dataWindowUI, text = " ", bg = "white").grid(row = 4, column = 0)
#Row 5
salesPriceExtLabel = tk.Label(dataWindowUI,text = "Sales Price Ext: ",bg = "white",fg =  "white")
salesPriceExtLabel.grid(row = 5, column = 0,sticky = tk.E)
#Row 6
totalCostExtLabel = tk.Label(dataWindowUI, text = "Total Cost Ext: ", bg = "white", fg =  "white")
totalCostExtLabel.grid(row = 6, column = 0, sticky = tk.E)
#Row 7
gmExtLabel = tk.Label(dataWindowUI, text = "GM Ext: ", bg = "white", fg =  "white")
gmExtLabel.grid(row = 7, column = 0, sticky = tk.E)
#Row 8
gmPercentLabel = tk.Label(dataWindowUI, text = "% GM: ", bg = "white", fg = "white")
gmPercentLabel.grid(row = 8, column = 0,sticky = tk.E)

################################################

#Window Column 1
#Row 0
stdLabel = tk.Label(dataWindowUI, text = "Standard:", bg = "white", fg =  "white")
stdLabel.grid(row = 0, column = 1,sticky = tk.W)
#Row 1
salesPriceUnitStdUI = tk.Label(dataWindowUI, bg = "white")
salesPriceUnitStdUI.grid(row = 1, column = 1, sticky = tk.W)
#Row 2
totalCostUnitStdUI = tk.Label(dataWindowUI, bg = "white")
totalCostUnitStdUI.grid(row = 2, column = 1, sticky = tk.W)
#Row 3
gmUnitStdUI = tk.Label(dataWindowUI, bg = "white")
gmUnitStdUI.grid(row = 3, column = 1, sticky = tk.W)
#Row 4
tk.Label(dataWindowUI, text = "                      ", bg = "white").grid(row = 4, column = 1)
#Row 5
salesPriceExtStdUI = tk.Label(dataWindowUI, bg = "white")
salesPriceExtStdUI.grid(row = 5, column = 1, sticky = tk.W)
#Row 6
totalCostExtStdUI = tk.Label(dataWindowUI, bg = "white")
totalCostExtStdUI.grid(row = 6, column = 1, sticky = tk.W)
#Row 7
gmExtStdUI = tk.Label(dataWindowUI, bg = "white")
gmExtStdUI.grid(row = 7, column = 1,sticky = tk.W)
#Row 8
gmPercentStdUI = tk.Label(dataWindowUI, bg = "white")
gmPercentStdUI.grid(row = 8, column = 1, sticky = tk.W)

################################################

#Window Column 2
#Row 0
tk.Label(dataWindowUI, text = "   ", bg = "white").grid(row = 0, column = 2)

################################################

#Window Column 3
#Row 0
actLabel = tk.Label(dataWindowUI, text = "Actual:", bg = "white", fg =  "white")
actLabel.grid(row = 0, column = 3,sticky = tk.W)
#Row 1
salesPriceUnitActUI = tk.Label(dataWindowUI, bg = "white")
salesPriceUnitActUI.grid(row = 1, column = 3, sticky = tk.W)
#Row 2
totalCostUnitActUI = tk.Label(dataWindowUI, bg = "white")
totalCostUnitActUI.grid(row = 2, column =  3, sticky = tk.W)
#Row 3
gmUnitActUI = tk.Label(dataWindowUI, bg = "white")
gmUnitActUI.grid(row = 3, column = 3, sticky = tk.W)
#Row 4
tk.Label(dataWindowUI, text = "                      ", bg = "white").grid(row = 4, column = 3)
#Row 5
salesPriceExtActUI = tk.Label(dataWindowUI, bg = "white")
salesPriceExtActUI.grid(row = 5, column = 3, sticky = tk.W)
#Row 6
totalCostExtActUI = tk.Label(dataWindowUI, bg = "white")
totalCostExtActUI.grid(row = 6, column = 3, sticky = tk.W)
#Row 7
gmExtActUI = tk.Label(dataWindowUI, bg = "white")
gmExtActUI.grid(row = 7, column = 3,sticky = tk.W)
#Row 8
gmPercentActUI = tk.Label(dataWindowUI, bg = "white")
gmPercentActUI.grid(row = 8, column = 3,sticky = tk.W)

#Other Info
################################################

#Window Column 4
#Row 0
tk.Label(dataWindowUI, text = "            ", bg = "white").grid(row = 0, column = 4)

################################################

#Window Column 5
#Row 0
customerLabel = tk.Label(dataWindowUI, text = "Customer: ", bg = "white", fg = "white")
customerLabel.grid(row = 0, column = 5, sticky = tk.E)
#Row 1
numJobsLabel = tk.Label(dataWindowUI,text = "Number of Jobs: ",bg = "white", fg = "white")
numJobsLabel.grid(row = 1, column = 5, sticky = tk.E)
#Row 2
avgLotLabel = tk.Label(dataWindowUI,text = "Average Lot Size: ",bg = "white", fg = "white")
avgLotLabel.grid(row = 2, column = 5, sticky = tk.E)
#Row 3
stdAccLabel = tk.Label(dataWindowUI, text = "Standard Accuracy: ", bg = "white", fg = "white")
stdAccLabel.grid(row = 3, column = 5,sticky = tk.E)
#Row 4
stdUpdateLabel = tk.Label(dataWindowUI, text = "Last Std Update: ", bg = "white", fg = "white")
stdUpdateLabel.grid(row = 4, column = 5,sticky = tk.E)
#Row 5
lastShipLabel = tk.Label(dataWindowUI, text = "Last Shipped: ", bg = "white", fg = "white")
lastShipLabel.grid(row = 5, column = 5,sticky = tk.E)
#Row 6
quoteNumLabel = tk.Label(dataWindowUI,text = "Last Quote Number: ",bg = "white", fg = "white")
quoteNumLabel.grid(row = 6, column = 5, sticky = tk.E)
#Row 7
lastQuoteDateLabel = tk.Label(dataWindowUI,text = "Last Quote Date: ",bg = "white", fg = "white")
lastQuoteDateLabel.grid(row = 7, column = 5, sticky = tk.E)
#Row 8
cellCodeLabel = tk.Label(dataWindowUI, text = "Cell Code: ", bg = "white", fg = "white")
cellCodeLabel.grid(row = 8, column = 5, sticky = tk.E)

################################################

#Window Column 6
#Row 0
customerUI = tk.Label(dataWindowUI, bg = "white")
customerUI.grid(row = 0, column = 6, sticky = tk.W)
#Row 1
numJobsUI = tk.Label(dataWindowUI,bg = "white")
numJobsUI.grid(row = 1, column = 6, sticky = tk.W)
#Row 2
avgLotUI = tk.Label(dataWindowUI,bg = "white")
avgLotUI.grid(row = 2, column = 6, sticky = tk.W)
#Row 3
stdAccUI = tk.Label(dataWindowUI, bg = "white")
stdAccUI.grid(row = 3, column = 6,sticky = tk.W)
#Row 4
stdUpdateUI = tk.Label(dataWindowUI, bg = "white")
stdUpdateUI.grid(row = 4, column = 6,sticky = tk.W)
#Row 5
lastShipUI = tk.Label(dataWindowUI, bg = "white")
lastShipUI.grid(row = 5, column = 6,sticky = tk.W)
#Row 6
quoteNumUI = tk.Label(dataWindowUI,bg = "white")
quoteNumUI.grid(row = 6, column = 6, sticky = tk.W)
#Row 7
lastQuoteDateUI = tk.Label(dataWindowUI,bg = "white")
lastQuoteDateUI.grid(row = 7, column = 6, sticky = tk.W)
#Row 8
cellCodeUI = tk.Label(dataWindowUI, bg = "white")
cellCodeUI.grid(row = 8, column = 6, sticky = tk.W)

################################################

#Window Column 7
#Row 0
tk.Label(dataWindowUI, text = "            ", bg = "white").grid(row = 0, column = 7)

################################################

#Window Column 8
#Row 0
laborBurdenLabel = tk.Label(dataWindowUI, text = "Labor + Burden: ", bg = "white", fg = "white")
laborBurdenLabel.grid(row = 0, column = 8, sticky = tk.W)
#Row 1
opLabel = tk.Label(dataWindowUI,text = "OP Cost: ", bg = "white", fg = "white")
opLabel.grid(row = 1, column = 8, sticky = tk.W)
#Row 2
materialLabel = tk.Label(dataWindowUI,text = "Material Cost: ", bg = "white", fg = "white")
materialLabel.grid(row = 2, column = 8, sticky = tk.W)


################################################

#Window Column 9
#Row 0
laborBurdenUI = tk.Label(dataWindowUI, bg = "white")
laborBurdenUI.grid(row = 0, column = 9, sticky = tk.W)
#Row 1
opUI = tk.Label(dataWindowUI,bg = "white")
opUI.grid(row = 1, column = 9, sticky = tk.W)
#Row 2
materialUI = tk.Label(dataWindowUI,bg = "white")
materialUI.grid(row = 2, column = 9, sticky = tk.W)


################################################


#Master Row 0
tk.Label(masterUI, text = "Part Number: ").grid(row = 0, column = 0, sticky = tk.E)
partEntryUI = tk.Entry(masterUI)
partEntryUI.grid(row = 0, column = 1)
partEntryUI.configure(width = 50)
#Master Row 1
tk.Label(masterUI, text = "Desired Margin: ").grid(row = 1, column = 0, sticky = tk.E)
desiredMarginUI = tk.Entry(masterUI)
desiredMarginUI.grid(row = 1, column = 1)
desiredMarginUI.configure(width = 50)
tk.Button(masterUI,text = 'Get Price Data',command = getData).grid(row=1, column=2, sticky=tk.W, pady=4)
tk.Label(masterUI, text = 'Default Margin 30%').place(x = 485, y = 27)

#Query Start Date
tk.Label(masterUI, text = "Query Start Date: %s" %(startDate)).grid(row = 0, column = 2, sticky = tk.W)

#Suggest Prices
tk.Label(masterUI, text = "Standard Suggested Unit Price: ").place(x = 25, y = 965) 
tk.Label(masterUI, text = "Actual Suggested Unit Price: ").place(x = 25, y = 985)

# Quit Button
tk.Button(masterUI, text = 'Quit Program' , command = masterUI.quit).place(x = 1825, y = 980)

#Point to master start
masterUI.mainloop()