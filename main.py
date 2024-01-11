import datetime
import random
import json
import time
import asyncio
import math
import os

print("Starting real-time stock generator v2024-01-09 v4")

from azure.eventhub import EventData
from azure.eventhub import EventHubProducerClient
from azure.identity import DefaultAzureCredential

#from azure.eventhub.aio import EventHubProducerClient
#from azure.identity.aio import DefaultAzureCredential
from enum import Enum

# Event Hub variables
EVENT_HUB_CONNECTION_STR = os.environ['EVENTHUBCONNECTIONSTRING']
EVENT_HUB_NAME = os.environ['EVENTHUBNAME']
EVENT_HUB_FQNS = os.environ['EVENTHUBFQNS']
USE_MANAGED_IDENTITY = True if int(os.environ['USEMANAGEDIDENTITY']) == 1 else False

PRINT_ONLY_ERRORS = True if int(os.environ['PRINTONLYERRORS']) == 1 else False
MAX_ERROR_COUNT = 15
USE_GROWTH_RATE =  True if int(os.environ['USEGROWTHRATE']) == 1 else False

# Stock variables
WHO_vars = os.environ['WHO_vars'].split('|')
WHAT_vars = os.environ['WHAT_vars'].split('|')
IDK_vars = os.environ['IDK_vars'].split('|')
WHY_vars = os.environ['WHY_vars'].split('|')
BCUZ_vars = os.environ['BCUZ_vars'].split('|')
TMRW_vars = os.environ['TMRW_vars'].split('|')
TDY_vars = os.environ['TDY_vars'].split('|')
IDGD_vars = os.environ['IDGD_vars'].split('|')

# ENV EVENTS '{"events": [{"type": "periodic", "name": "300-up", "frequency":300, "increasechance":1.0, "duration": 5,
# "modifier": 0.5},{"type": "periodic", "name": "900-down", "frequency":900, "increasechance":0.0, "duration": 10, "modifier": 0.5},
# {"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.25}]}'
EventsJson = os.environ['EVENTS']

#'{"timers": [{"name": "Business Hours", "start":"00:00:00", "end":"07:00:00", "modifier":0.99, "appliedTo": "WHO|WHAT|IDK"}, {"name": "Hour of Darkness", "start":"00:00:00", "end":"08:00:00", "modifier":-0.99, "appliedTo": "TMRW"}]}'
TimersJson = os.environ['TIMERS']

SkipEventHub = True if int(os.environ['SKIPEVENTHUB']) == 1 else False

if SkipEventHub:
    print("Skipping Event Hub - events will not be sent to Event Hub")

# Extended stock info is intended to help show correlation on the data on the backend
# by including events (up or down) in the data feed (stockEvent and marketEvent)
ExtendedStockInfo = True if int(os.environ['EXTENDEDSTOCKINFO']) == 1 else False

# stock variables: 0 start price | 1 min price | 2 max price | 3 mu | 4 sigma | 
# 5 correction chance | 6 correction length | 7 correction modifier |
# 8 0-20 increase chance | 9 20-40 increase chance | 10 40-60 | 11 60-80 | 12 80-100

growthInceptionDate = datetime.datetime.strptime("2023-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
timestamp = datetime.datetime.utcnow()

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
        self.growthRateAnnual = float(stockVariables[13])
        self.growthRateDaily = self.growthRateAnnual / 365
    
    def getMaxPrice(self):
        if USE_GROWTH_RATE and self.growthRateAnnual != 0:
            # get days since inception
            daysSinceInception = (timestamp - growthInceptionDate).days
            # calculate growth rate
            growthRateModifier = math.pow(1 + self.growthRateDaily, daysSinceInception)
            # apply growth rate
            newMaxPrice = self.maxPrice * growthRateModifier
            # make sure new max price is greater than min price
            if newMaxPrice < (self.minPrice + 1):
                self.growthRateDaily = abs(self.growthRateDaily)
                newMaxPrice = self.minPrice + 1
                
            return newMaxPrice
        else:
            return self.maxPrice
    
    def getPriceRange(self):
        return self.currentPrice / (self.getMaxPrice() - self.minPrice)
    
    def getIncreaseChance(self, timerModifier = 0.0):

        r = self.getPriceRange()
        increaseChance = self.increaseChance_0_20
        if (r >= 0.80): increaseChance = self.increaseChance_80_100
        elif (r >= 0.60): increaseChance = self.increaseChance_60_80
        elif (r >= 0.40): increaseChance = self.increaseChance_40_60
        elif (r >= 0.20): increaseChance = self.increaseChance_20_40

        increaseChance = increaseChance + timerModifier
        if increaseChance < 0.0: increaseChance = 0.0
        if increaseChance > 1.0: increaseChance = 1.0
        
        return increaseChance

print(f"EVENT_HUB_NAME: {EVENT_HUB_NAME}")
print(f"EVENT_HUB_CONNECTION_STR: {EVENT_HUB_CONNECTION_STR}")
print(f"EVENT_HUB_FQNS: {EVENT_HUB_FQNS}")
print(f"USE_MANAGED_IDENTITY: {USE_MANAGED_IDENTITY}")

print("")

print("WHO: ", WHO_vars)
print("WHAT: ", WHAT_vars)
print("IDK: ", IDK_vars)
print("WHY: ", WHY_vars)
print("BCUZ: ", BCUZ_vars)
print("TMRW: ", TMRW_vars)
print("TDY: ", TDY_vars)
print("IDGD: ", IDGD_vars)
print("Events JSON: ", EventsJson)
print("Timers JSON: ", TimersJson)
print("Growth rate: ", USE_GROWTH_RATE)

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
numTimers = 0

class MessageType(Enum):
    INFO = 1
    ERROR = 2

def printMsg(message, messageType = MessageType.INFO):
    if (PRINT_ONLY_ERRORS == False) or (PRINT_ONLY_ERRORS and messageType == MessageType.ERROR):
        print(message)

try:
    AllEvents = json.loads(EventsJson)
    numEvents = len(AllEvents['events'])

    if numEvents > 0:
        for event in AllEvents['events']:
            event['durationCount'] = event['duration']
            if (event['type'] == 'periodic'):
                event['frequencyCount'] = event['frequency']
            print(f'Event: {event["name"]} {str(event["type"])} {str(event["frequency"])}' \
                f'{str(event["duration"])} {str(event["increasechance"])}')
        
except Exception as e:
    numEvents = 0
    print("Error parsing JSON, continuing without events.")
    print(e)
        
try:
    AllTimers = json.loads(TimersJson)
    numTimers = len(AllTimers['timers'])

    if numTimers > 0:
        for timer in AllTimers['timers']:
            timer['start'] = datetime.datetime.strptime(timer['start'], "%H:%M:%S").time()
            timer['end'] = datetime.datetime.strptime(timer['end'], "%H:%M:%S").time()
            print(f'Timer: {timer["name"]} {str(timer["start"])} {str(timer["end"])} ' \
                f'{str(timer["days"])} {str(timer["dayofmonth"])} {str(timer["months"])} {str(timer["appliedTo"])} {str(timer["modifier"])}') 
            
except Exception as e:
    numTimers = 0
    print(f"{datetime.datetime.utcnow()} Error parsing JSON, continuing without timers. {e}")


totalInitialMarketCap = 0
for record in dataTable:
    totalInitialMarketCap = totalInitialMarketCap + record[1].startPrice
    
async def run():

    #create event hub connection using either managed identity or connection string
    if USE_MANAGED_IDENTITY:
        #create a producer client using system assigned managed identity
        print("Configuring event hub to use managed identity")
        print("Sleeping for 20s for managed identity deployment")
        time.sleep(20)
        credential = DefaultAzureCredential()
        producer = EventHubProducerClient(fully_qualified_namespace=EVENT_HUB_FQNS, 
                                          eventhub_name=EVENT_HUB_NAME,
                                          credential=credential)
    else:
        #create a producer client using SAS key authentication
        print("Configuring event hub to use SAS key")
        producer = EventHubProducerClient.from_connection_string(
            conn_str=EVENT_HUB_CONNECTION_STR, eventhub_name=EVENT_HUB_NAME)


    # async with producer:

    isEvent = False
    currentEvent = ""
    count = 0
    aboveMarketCount = 1
    belowMarketCount = 1
    errorCount = 0

    while True:
        
        timestamp = datetime.datetime.utcnow()
        event_data_batch = None

        if not SkipEventHub:
            try:
                event_data_batch = producer.create_batch() # create a batch
            except Exception as e:
                    errorCount += 1
                    printMsg(f"{datetime.datetime.utcnow()} Error creating batch ({errorCount}) - {e}", MessageType.ERROR)

        if numEvents > 0 and isEvent == False:
            for event in AllEvents['events']:
                if (event['type'] == 'periodic' and event['frequencyCount'] <= 0):
                    # periodic event triggered
                    event['frequencyCount'] = event['frequency']
                    event['durationCount'] = event['duration']
                    event['isIncreasing'] = random.random() < event['increasechance']
                    currentEvent = event
                    isEvent = True
                    printMsg(f'{event["name"]} Event Triggered ({"UP" if event["isIncreasing"] else "DOWN"})')
                    break
                elif (event['type'] == 'random' and random.random() < event['frequency']):
                    # random event triggered
                    event['durationCount'] = event['duration']
                    event['isIncreasing'] = random.random() < event['increasechance']
                    currentEvent = event
                    isEvent = True
                    printMsg(f'{event["name"]} Event Triggered ({"UP" if event["isIncreasing"] else "DOWN"})')
                    break

        totalMarketCap = 0

        for record in dataTable:

            symbol = record[0]
            stockVariables = record[1]
            price = stockVariables.currentPrice

            # apply timers
            # modifier is cumulative across all timers
            currentTimerModifier = 0.0
            appliedTimers = 0
            if numTimers > 0:
                for timer in AllTimers['timers']:
                    if (timer['start'] <= timestamp.time() <= timer['end'] 
                            and (timer['appliedTo'] == 'all' or symbol in timer['appliedTo'].split('|'))
                            and str(timestamp.weekday()) in timer['days'].split('|')
                            and str(timestamp.month) in timer['months'].split('|')
                            and (timer['dayofmonth'] == 'all' or str(timestamp.day) in timer['dayofmonth'].split('|'))
                            ):
                        currentTimerModifier += timer['modifier']
                        appliedTimers += 1

            # priceIncDec = abs(price - (random.normalvariate(stockVariables.mu, stockVariables.sigma) * price))
            priceIncDec = abs(round(random.normalvariate(stockVariables.mu, stockVariables.sigma),2))

            priceIncrease = random.random() < stockVariables.getIncreaseChance(currentTimerModifier)

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
                    stockVariables.isCorrectionUpwards = random.random() < stockVariables.getIncreaseChance(currentTimerModifier)
                    printMsg(f'{symbol} Correction ({"UP" if stockVariables.isCorrectionUpwards else "DOWN"})')

            if stockVariables.isInCorrection:
                if stockVariables.correctionCounter <= 0:
                    stockVariables.isInCorrection = False
                else:
                    priceIncrease = stockVariables.isCorrectionUpwards # force direction if in correction
                    priceIncDec = priceIncDec * stockVariables.correctionModifier # make corrections more gradual
                    stockVariables.correctionCounter -= 1

            if priceIncrease:
                newPrice = round(price + priceIncDec,2)
                # newPrice = (newPrice if newPrice < stockVariables.maxPrice else stockVariables.maxPrice)
                newPrice = round(newPrice if newPrice < stockVariables.getMaxPrice() else stockVariables.getMaxPrice(),2)
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
            
            extendedStockValue = 0 
            if stockVariables.isInCorrection:
                extendedStockValue = 1 if stockVariables.isCorrectionUpwards else -1

            extendedMarketValue = 0
            if isEvent:
                extendedMarketValue = 1 if currentEvent['isIncreasing'] else -1

            if ExtendedStockInfo:
                reading = {'symbol': symbol, 'price': newPrice, 'timestamp': str(timestamp), 
                            'stockEvent': extendedStockValue,
                            'marketEvent': extendedMarketValue,
                            'timer': appliedTimers #1 if isTimer else 0
                            }
            else:
                reading = {'symbol': symbol, 'price': newPrice, 'timestamp': str(timestamp)}

            s = json.dumps(reading)

            printMsg(s + 
                    f' O/U:{stockVariables.aboveStartingCount/stockVariables.belowStartingCount:.2f} ' + 
                    f'| U/D:{stockVariables.moveUpCount/stockVariables.moveDownCount:.2f} ' +
                    f'| R:{stockVariables.getPriceRange():.2f} ' +
                    f'| IC:{stockVariables.getIncreaseChance(currentTimerModifier):.4f} ' + 
                    f'| T:{appliedTimers} ' + #{1 if isTimer else 0} ' +
                    f'| M:{extendedMarketValue} ' +
                    f'| S:{extendedStockValue}')

            if not SkipEventHub:
                try:
                    if not event_data_batch is None: 
                        event_data_batch.add(EventData(s)) # add event data to the batch
                except Exception as e:
                    errorCount += 1
                    printMsg(f"{datetime.datetime.utcnow()} Error adding to batch ({errorCount}) - {e}", MessageType.ERROR)

            totalMarketCap = totalMarketCap + newPrice

        if not SkipEventHub:
            try:
                # send the batch of events to the event hub
                producer.send_batch(event_data_batch)
                errorCount = 0
            except Exception as e:
                errorCount += 1
                printMsg(f"{datetime.datetime.utcnow()} Error sending batch ({errorCount}) - {e}", MessageType.ERROR)
                if (errorCount > MAX_ERROR_COUNT):
                    printMsg(f"{datetime.datetime.utcnow()} Too many errors, raising exception", MessageType.ERROR)
                    raise e

        if (totalMarketCap >= totalInitialMarketCap):
            aboveMarketCount += 1
        else:
            belowMarketCount += 1
        
        if isEvent:
            printMsg(f'{count} | Total Cap: {totalMarketCap:.2f} | ' +
            f'Avg: {totalMarketCap/len(dataTable):.2f} | ' +
            f'O/U: {aboveMarketCount/belowMarketCount:.2f} | ' + 
            f'Event: {currentEvent["name"]} ({currentEvent["durationCount"]})')
        
        else:
            printMsg(f'{count} | Total Cap: {totalMarketCap:.2f} | ' +
            f'Avg: {totalMarketCap/len(dataTable):.2f} | ' +
            f'O/U: {aboveMarketCount/belowMarketCount:.2f}')
                
        # update counters 
        count += 1

        if isEvent:
            currentEvent["durationCount"] -= 1
        
        if numEvents > 0:
            for event in AllEvents['events']:
                if (event['type'] == 'periodic'):
                    event['frequencyCount'] -= 1
            
        time.sleep(1)

asyncio.run(run())