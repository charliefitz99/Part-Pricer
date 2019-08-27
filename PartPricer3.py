import tkinter as tk
import string
import pymssql

f = open("userpass.txt","r")
contents = f.read().splitlines()
#Epicor Connection
conn = pymssql.connect(server=contents[0],port=1433, user=contents[1], password=contents[2], database="epicor10")
cursor = conn.cursor()
#Query Start Date
startDate = "2019-01-01"

#Starts SQL query and sets up display
def getData():    
    partNumber = partEntryUI.get()
    marginString = desiredMarginUI.get()
    if marginString == "":
        margin = 30
    else:
        margin = float(marginString)
    sqlQuery(partNumber)
    print(currentPrice)
    print("global currentPrice " + str(currentPrice))
    print("global extGM " + str(extGM))
    print("global stdUnit " + str(stdUnit))
    print("global totalQty " + str(totalQty))
    print("global totalCost " + str(totalCost))
    print("global totalRevenue " + str(totalRevenue))
    print("Num Jobs: " + str(len(jobs)))
    
    #Configure output
    currentPriceLabel.configure(fg = "black")
    currentPriceUI.configure(text = str(currentPrice))
    
    extActGMLabel.configure(fg = "black")
    extActGMColor = "red" if extGM < 0 else "black"
    extActGMUI.configure(text = str(round(extGM,2)),fg = extActGMColor)
    
    stdUnitLabel.configure(fg = "black")
    stdUnitUI.configure(text = str(round(stdUnit, 2)))
    
    actUnitLabel.configure(fg = "black")
    actUnitUI.configure(text = str(round(avgUnitCost, 2)))
    
    stdAccuracy = getStdAcc()
    stdAccLabel.configure(fg = "black")
    stdAccColor = "red" if stdAccuracy > .35 or stdAccuracy < -.35 else "green"
    stdAccUI.configure(text = str(round(stdAccuracy, 2)), fg = stdAccColor)
    
    stdUpdateLabel.configure(fg = "black")
    stdUpdateUI.configure(text = lastStdUpdate)
    
    customerLabel.configure(fg = "black")
    customerUI.configure(text = customer)
    
    lastShipLabel.configure(fg = "black")
    lastShipUI.configure(text = lastShipDate)  
    
    avgLotLabel.configure(fg = "black")
    avgLotUI.configure(text = round(getAvgLotSize(),2))
    
    laborBurdenLabel.configure(fg = "black")
    laborBurdenUI.configure(text = str(int(round(getPercentLaborBurden(),2)*100))+"%")
    
    materialLabel.configure(fg = "black")
    materialUI.configure(text = str(int(round(getPercentMaterial(),2)*100))+ "%")
    
    opLabel.configure(fg = "black")
    opUI.configure(text = str(int(round(getPercentOP(),2)*100)) + "%")
    
    scrapLabel.configure(fg = "black")
    scrapUI.configure(text = str(round(getPercentScrap(),2)*100) + "%")
    
    numJobsLabel.configure(fg = "black")
    numJobsUI.configure(text = str(len(jobs)))
    
    quoteNumLabel.configure(fg = "black")
    quoteNumUI.configure(text = quoteNumber)
    
    lastQuoteDateLabel.configure(fg = "black")
    lastQuoteDateUI.configure(text = lastQuoteDate)
    
    tk.Label(masterUI, text = "                             ").place(x = 175, y = 985)
    actSuggestPriceUI = tk.Label(masterUI, text = str(round(getSuggestActPrice(margin),2))).place(x = 170 , y = 985)
    
    tk.Label(masterUI, text = "                              ").place(x = 175, y = 965)
    stdSuggestPriceUI = tk.Label(masterUI, text = str(round(getSuggestStdPrice(margin),2))).place(x = 170 , y = 965)        
    
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
    
    #Global Arrays
    global jobs
    global jobQtys
    global laborExtCosts
    global burdenExtCosts
    global materialExtCosts
    global opExtCosts
    global shipQtys
    global totalShipped
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
    cursor.execute("SELECT LotNum FROM Erp.PartLot WHERE PartNum = '{}' AND LastRefDate >= '{}' ORDER BY LastRefDate".format(partNumber,startDate))
    jobs = cursorTranslate(cursor.fetchall())
    
    #Get ship quantities by date from ship detail
    cursor.execute("SELECT OurInventoryShipQty FROM Erp.shipdtl WHERE PartNum = '{}' AND ChangeDate >= '{}'".format(partNumber,startDate)) 
    shipQtys = cursorTranslateFloat(cursor.fetchall())
    totalShipped = 0
    for shipDtl in shipQtys:
        totalShipped = totalShipped + shipDtl
    
    # Get Job Quantities by date
    for job in jobs:
        #Get issued quantities
        cursor.execute("SELECT ProdQty from erp.jobhead where JobNum = '%s'" %(job))
        issueQtys.append(cursorTranslateFloatSingle(cursor.fetchall()))
        cursor.execute("SELECT QtyCompleted from erp.jobhead where JobNum = '%s'" %(job)) 
        actComplete.append(cursorTranslateFloatSingle(cursor.fetchall()))
        #actual qtys
        cursor.execute("SELECT QtyCompleted from erp.jobhead where JobNum = '%s'" %(job))
        if cursorTranslateFloatSingle(cursor.fetchall()) <= 0:
            cursor.execute("SELECT ProdQty from erp.jobhead where JobNum = '%s'" %(job))
        else:
            cursor.execute("SELECT QtyCompleted from erp.jobhead where JobNum = '%s'" %(job))    
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
    
    #Get lastShipDate
    cursor.execute("SELECT ChangeDate FROM Erp.shipdtl WHERE PartNum = '{}' AND ChangeDate >= '{}' ORDER BY changeDate".format(partNumber,startDate))
    shipDates = cursorTranslate(cursor.fetchall())
    for date in shipDates:
        lastShipDate = date
        
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

#Column 0/1
#Window Row 0
currentPriceLabel = tk.Label(dataWindowUI,text = "Current Price: ",bg = "white",fg = "white")
currentPriceLabel.grid(row = 0, column = 0,sticky = tk.W)
currentPriceUI = tk.Label(dataWindowUI,bg = "white")
currentPriceUI.grid(row = 0, column = 1,sticky = tk.W)
#Window Row 1
extActGMLabel = tk.Label(dataWindowUI,text = "Extended GM: ", bg = "white",fg = "white")
extActGMLabel.grid(row = 1, column = 0,sticky = tk.W)
extActGMUI = tk.Label(dataWindowUI,bg = "white")
extActGMUI.grid(row = 1, column = 1,sticky = tk.W)
#Window Row 2
stdUnitLabel = tk.Label(dataWindowUI, text = "Standard Unit Cost: ", bg = "white", fg = "white")
stdUnitLabel.grid(row = 2, column = 0,sticky = tk.W)
stdUnitUI = tk.Label(dataWindowUI, bg = "white")
stdUnitUI.grid(row = 2, column = 1, sticky = tk.W)
#Window Row 3
actUnitLabel = tk.Label(dataWindowUI, text = "Avg Act Unit Cost: ", bg = "white", fg = "white")
actUnitLabel.grid(row = 3, column = 0,sticky = tk.W)
actUnitUI = tk.Label(dataWindowUI, bg = "white")
actUnitUI.grid(row = 3, column = 1, sticky = tk.W)
#Window Row 4
stdAccLabel = tk.Label(dataWindowUI, text = "Standard Accuracy: ", bg = "white", fg = "white")
stdAccLabel.grid(row = 4, column = 0,sticky = tk.W)
stdAccUI = tk.Label(dataWindowUI, bg = "white")
stdAccUI.grid(row = 4, column = 1, sticky = tk.W)
#Window Row 5
stdUpdateLabel = tk.Label(dataWindowUI, text = "Last Std Update: ", bg = "white", fg = "white")
stdUpdateLabel.grid(row = 5, column = 0,sticky = tk.W)
stdUpdateUI = tk.Label(dataWindowUI, bg = "white")
stdUpdateUI.grid(row = 5, column = 1, sticky = tk.W)
#Window Row 6
lastShipLabel = tk.Label(dataWindowUI, text = "Last Shipped: ", bg = "white", fg = "white")
lastShipLabel.grid(row = 6, column = 0,sticky = tk.W)
lastShipUI = tk.Label(dataWindowUI, bg = "white")
lastShipUI.grid(row = 6, column = 1, sticky = tk.W)


#Column 2
spacerLabel = tk.Label(dataWindowUI, text = "                           ",bg = "white",fg = "white")
spacerLabel.grid(row = 0, column = 2,sticky = tk.W)

#Column 3/4
#Window Row 0
customerLabel = tk.Label(dataWindowUI, text = "Customer: ", bg = "white", fg = "white")
customerLabel.grid(row = 0, column = 3, sticky = tk.W)
customerUI = tk.Label(dataWindowUI, bg = "white")
customerUI.grid(row = 0, column = 4, sticky = tk.W)
#Window Row 1
avgLotLabel = tk.Label(dataWindowUI,text = "Average Lot Size: ",bg = "white", fg = "white")
avgLotLabel.grid(row = 1, column = 3, sticky = tk.W)
avgLotUI = tk.Label(dataWindowUI, bg = "white")
avgLotUI.grid(row = 1, column = 4, sticky = tk.W)
#Window Row 2
numJobsLabel = tk.Label(dataWindowUI,text = "Number of Jobs: ",bg = "white", fg = "white")
numJobsLabel.grid(row = 2, column = 3, sticky = tk.W)
numJobsUI = tk.Label(dataWindowUI, bg = "white")
numJobsUI.grid(row = 2, column = 4, sticky = tk.W)
#Window Row 3
scrapLabel = tk.Label(dataWindowUI,text = "Avg Scrap: ",bg = "white", fg = "white")
scrapLabel.grid(row = 3, column = 3, sticky = tk.W)
scrapUI = tk.Label(dataWindowUI, bg = "white")
scrapUI.grid(row = 3, column = 4, sticky = tk.W)
#Window Row 4
quoteNumLabel = tk.Label(dataWindowUI,text = "Last Quote Number: ",bg = "white", fg = "white")
quoteNumLabel.grid(row = 4, column = 3, sticky = tk.W)
quoteNumUI = tk.Label(dataWindowUI, bg = "white")
quoteNumUI.grid(row = 4, column = 4, sticky = tk.W)
#Window Row 5
lastQuoteDateLabel = tk.Label(dataWindowUI,text = "Last Quote Date: ",bg = "white", fg = "white")
lastQuoteDateLabel.grid(row = 5, column = 3, sticky = tk.W)
lastQuoteDateUI = tk.Label(dataWindowUI, bg = "white")
lastQuoteDateUI.grid(row = 5, column = 4, sticky = tk.W)


#Column 5
spacerLabel = tk.Label(dataWindowUI, text = "                           ",bg = "white",fg = "white")
spacerLabel.grid(row = 0, column = 5,sticky = tk.W)

#Column 6/7
#Window Row 2
laborBurdenLabel = tk.Label(dataWindowUI,text = "Labor + Burden Cost: ",bg = "white", fg = "white")
laborBurdenLabel.grid(row = 0, column = 6, sticky = tk.W)
laborBurdenUI = tk.Label(dataWindowUI, bg = "white")
laborBurdenUI.grid(row = 0, column = 7, sticky = tk.W)
#Window Row 3
materialLabel = tk.Label(dataWindowUI,text = "Material Cost: ",bg = "white", fg = "white")
materialLabel.grid(row = 1, column = 6, sticky = tk.W)
materialUI = tk.Label(dataWindowUI, bg = "white")
materialUI.grid(row = 1, column = 7, sticky = tk.W)
#Window Row 4
opLabel = tk.Label(dataWindowUI,text = "OP Cost: ",bg = "white", fg = "white")
opLabel.grid(row = 2, column = 6, sticky = tk.W)
opUI = tk.Label(dataWindowUI, bg = "white")
opUI.grid(row = 2, column = 7, sticky = tk.W)

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
tk.Label(masterUI, text = "Standard Suggested Price: ").place(x = 25, y = 965) 
tk.Label(masterUI, text = "Actual Suggested Price: ").place(x = 25, y = 985)

# Quit Button
tk.Button(masterUI, text = 'Quit Program' , command = masterUI.quit).place(x = 1825, y = 980)

#Point to master start
masterUI.mainloop()