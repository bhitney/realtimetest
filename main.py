import datetime
import random
import json
import time
import asyncio
import math
import os

print("Starting...")

from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient

EVENT_HUB_CONNECTION_STR = os.environ['EVENTHUBCONNECTIONSTRING']
EVENT_HUB_NAME = os.environ['EVENTHUBNAME']

WHO_vars = os.environ['WHO_vars'].split('|')
WHAT_vars = os.environ['WHAT_vars'].split('|')
IDK_vars = os.environ['IDK_vars'].split('|')
WHY_vars = os.environ['WHY_vars'].split('|')
BCUZ_vars = os.environ['BCUZ_vars'].split('|')
TMRW_vars = os.environ['TMRW_vars'].split('|')
TDY_vars = os.environ['TDY_vars'].split('|')
IDGD_vars = os.environ['IDGD_vars'].split('|')

EventsJson = os.environ['EVENTS']

# Extended stock info is intended to help show correlation on the data on the backend
# by including events (up or down) in the data feed
ExtendedStockInfo = int(os.environ['EXTENDEDSTOCKINFO'])

# stock variables: 0 start price | 1 min price | 2 max price | 3 mu | 4 sigma | 
# 5 correction chance | 6 correction length | 7 correction modifier |
# 8 0-20 increase chance | 9 20-40 increase chance | 10 40-60 | 11 60-80 | 12 80-100

class StockVariables:
    def __init__(self, stockVariables) -> None:
        self.startPrice = float(stockVariables[0])
        self.minPrice = float(stockVariables[1])
        self.maxPrice = float(stockVariables[2])
        self.currentPrice = float(stockVariables[0])
        self.mu = float(stockVariables[3])
        self.sigma = float(stockVariables[4])
        self.correctionChance = float(stockVariables[5])
        self.correctionLength = int(stockVariables[6])
        self.correctionCounter = 0
        self.correctionModifier = float(stockVariables[7])
        self.isInCorrection = False
        self.isCorrectionUpwards = True
        self.aboveStartingCount = 1
        self.belowStartingCount = 1
        self.moveUpCount = 1
        self.moveDownCount = 1
        self.increaseChance_0_20 = float(stockVariables[8])
        self.increaseChance_20_40 = float(stockVariables[9])
        self.increaseChance_40_60 = float(stockVariables[10])
        self.increaseChance_60_80 = float(stockVariables[11])
        self.increaseChance_80_100 = float(stockVariables[12])

    def getPriceRange(self):
        return self.currentPrice / (self.maxPrice - self.minPrice)
    
    def getIncreaseChance(self):
        r = self.getPriceRange()
        if (r >= 0.80): return self.increaseChance_80_100
        if (r >= 0.60): return self.increaseChance_60_80
        if (r >= 0.40): return self.increaseChance_40_60
        if (r >= 0.20): return self.increaseChance_20_40
        return self.increaseChance_0_20

print("EventHub: " + EVENT_HUB_NAME)
print("EventHubConnString: " + EVENT_HUB_CONNECTION_STR)

print("WHO: ", WHO_vars)
print("WHAT: ", WHAT_vars)
print("IDK: ", IDK_vars)
print("WHY: ", WHY_vars)
print("BCUZ: ", BCUZ_vars)
print("TMRW: ", TMRW_vars)
print("TDY: ", TDY_vars)
print("IDGD: ", IDGD_vars)
print("Events JSON: ", EventsJson)

dataTable = [
     ['WHO', StockVariables(WHO_vars)] 
    ,['WHAT', StockVariables(WHAT_vars)] 
    ,['IDK', StockVariables(IDK_vars)] 
    ,['WHY', StockVariables(WHY_vars)] 
    ,['BCUZ', StockVariables(BCUZ_vars)] 
    ,['TMRW', StockVariables(TMRW_vars)] 
    ,['TDY', StockVariables(TDY_vars)] 
    ,['IDGD', StockVariables(IDGD_vars)] 
    ]

numEvents = 0


try:
    AllEvents = json.loads(EventsJson)
    numEvents = len(AllEvents['events'])
except Exception as e:
    numEvents = 0
    print("Error parsing JSON, continuing without events.")
    print(e)

if numEvents > 0:
    for event in AllEvents['events']:
        event['durationCount'] = event['duration']
        if (event['type'] == 'periodic'):
            event['frequencyCount'] = event['frequency']
        
totalInitialMarketCap = 0
for record in dataTable:
    totalInitialMarketCap = totalInitialMarketCap + record[1].startPrice
    
async def run():

    # Create a producer client to send messages to the event hub.
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STR, eventhub_name=EVENT_HUB_NAME
    )

    async with producer:

        isEvent = False
        currentEvent = ""
        count = 0
        aboveMarketCount = 1
        belowMarketCount = 1
        errorCount = 0

        while True:
            
            timestamp = str(datetime.datetime.utcnow())

            try:
                event_data_batch = await producer.create_batch() # create a batch
            except Exception as e:
                    errorCount += 1
                    print(f"Error creating batch, continuing ({errorCount}).")
                    print(e)

            if numEvents > 0 and isEvent == False:
                for event in AllEvents['events']:
                    if (event['type'] == 'periodic' and event['frequencyCount'] <= 0):
                        # periodic event triggered
                        event['frequencyCount'] = event['frequency']
                        event['durationCount'] = event['duration']
                        event['isIncreasing'] = random.random() < event['increasechance']
                        currentEvent = event
                        isEvent = True
                        print(event['name'] + " Event Triggered (" + ("UP" if event['isIncreasing'] else "DOWN") + ")")
                        break
                    elif (event['type'] == 'random' and random.random() < event['frequency']):
                        # random event triggered
                        event['durationCount'] = event['duration']
                        event['isIncreasing'] = random.random() < event['increasechance']
                        currentEvent = event
                        isEvent = True
                        print(event['name'] + " Event Triggered (" + ("UP" if event['isIncreasing'] else "DOWN") + ")")
                        break

            totalMarketCap = 0

            for record in dataTable:

                symbol = record[0]
                stockVariables = record[1]
                price = stockVariables.currentPrice

                priceIncDec = abs(price - (random.normalvariate(stockVariables.mu, stockVariables.sigma) * price))
                priceIncrease = random.random() < stockVariables.getIncreaseChance()
 
                if isEvent:
                    if currentEvent['durationCount'] <= 0:
                        isEvent = False
                    else:
                        priceIncrease = currentEvent['isIncreasing'] # force direction if in correction
                        priceIncDec = priceIncDec * currentEvent['modifier'] # make corrections more gradual
                    stockVariables.isInCorrection = False # force individual corrections off if event

                else:
                    if stockVariables.isInCorrection == False and random.random() < stockVariables.correctionChance:
                        stockVariables.isInCorrection = True
                        stockVariables.correctionCounter = stockVariables.correctionLength
                        stockVariables.isCorrectionUpwards = random.random() < stockVariables.getIncreaseChance()
                        print(symbol + " Correction (" + ("UP" if stockVariables.isCorrectionUpwards else "DOWN") + ")")

                if stockVariables.isInCorrection:
                    if stockVariables.correctionCounter <= 0:
                        stockVariables.isInCorrection = False
                    else:
                        priceIncrease = stockVariables.isCorrectionUpwards # force direction if in correction
                        priceIncDec = priceIncDec * stockVariables.correctionModifier # make corrections more gradual
                        stockVariables.correctionCounter -= 1

                if priceIncrease:
                    newPrice = round(price + priceIncDec,2)
                    newPrice = (newPrice if newPrice < stockVariables.maxPrice else stockVariables.maxPrice)
                    stockVariables.moveUpCount += 1
                    #increase
                else:
                    newPrice = round(price - priceIncDec,2)
                    newPrice = (newPrice if newPrice > stockVariables.minPrice else stockVariables.minPrice)
                    stockVariables.moveDownCount += 1
                    #decrease

                stockVariables.currentPrice = newPrice
                if (stockVariables.currentPrice > stockVariables.startPrice):
                    stockVariables.aboveStartingCount += 1
                else:
                    stockVariables.belowStartingCount += 1
                
                record[1] = stockVariables
                
                if ExtendedStockInfo == 1:
                    reading = {'symbol': symbol, 'price': newPrice, 'timestamp': timestamp, 
                               'stockEvent': 1 if stockVariables.isInCorrection == True else 0,
                               'marketEvent': 1 if isEvent == True else 0 
                               }
                else:
                    reading = {'symbol': symbol, 'price': newPrice, 'timestamp': timestamp}

                s = json.dumps(reading)
                if stockVariables.isInCorrection:
                    print(s + " (" + ("UP" if stockVariables.isCorrectionUpwards else "DOWN") + ")")
                else:
                    print(s + f' (+/-: {stockVariables.aboveStartingCount - stockVariables.belowStartingCount}) ' +
                        f'(O/U: {stockVariables.aboveStartingCount/stockVariables.belowStartingCount:.2f}) ' + 
                        f'(U/D: {stockVariables.moveUpCount/stockVariables.moveDownCount:.2f}) ' +
                        f'(R: {stockVariables.getPriceRange():.2f}) ' +
                        f'(IC: {stockVariables.getIncreaseChance():.4f})')

                try:
                    event_data_batch.add(EventData(s)) # add event data to the batch
                except Exception as e:
                    errorCount += 1
                    print(f"Error adding to batch, continuing ({errorCount}).")
                    print(e)

                totalMarketCap = totalMarketCap + newPrice

            try:
                # send the batch of events to the event hub
                await producer.send_batch(event_data_batch)
                errorCount = 0
            except Exception as e:
                errorCount += 1
                print(f"Error sending batch, continuing ({errorCount}).")
                print(e)
                if (errorCount > 15):
                    print("Too many errors, bubbling exception.")
                    raise e

            if (totalMarketCap >= totalInitialMarketCap):
                aboveMarketCount += 1
            else:
                belowMarketCount += 1

            if isEvent:
                print(f'{count} | Total Cap: {totalMarketCap:.2f} | ' +
                f'Avg: {totalMarketCap/len(dataTable):.2f} | ' +
                f'O/U: {aboveMarketCount/belowMarketCount:.2f} | ' + 
                f'Event: {currentEvent["name"]} ({currentEvent["durationCount"]})')
               
            else:
                print(f'{count} | Total Cap: {totalMarketCap:.2f} | ' +
                f'Avg: {totalMarketCap/len(dataTable):.2f} | ' +
                f'O/U: {aboveMarketCount/belowMarketCount:.2f}')
                    
            count += 1

            if isEvent:
                currentEvent["durationCount"] -= 1
            
            if numEvents > 0:
                for event in AllEvents['events']:
                    if (event['type'] == 'periodic'):
                        event['frequencyCount'] -= 1
                
            time.sleep(1)

asyncio.run(run())