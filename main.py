import datetime
import random
import json
import time
import asyncio
import math
import os

print("Starting real-time stock generator - 2024-03-02 v6")

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
WARM_UP_HOURS = int(os.environ['WARMUPHOURS'])

isWarmup = True if WARM_UP_HOURS > 0 else False

# Stock variables
# WHO_vars = os.environ['WHO_vars'].split('|')
# WHAT_vars = os.environ['WHAT_vars'].split('|')
# IDK_vars = os.environ['IDK_vars'].split('|')
# WHY_vars = os.environ['WHY_vars'].split('|')
# BCUZ_vars = os.environ['BCUZ_vars'].split('|')
# TMRW_vars = os.environ['TMRW_vars'].split('|')
# TDY_vars = os.environ['TDY_vars'].split('|')
# IDGD_vars = os.environ['IDGD_vars'].split('|')

StocksJson = os.environ['STOCKS']

# ENV EVENTS '{"events": [{"type": "periodic", "name": "300-up", "frequency":300, "increasechance":1.0, "duration": 5,
# "modifier": 0.5},{"type": "periodic", "name": "900-down", "frequency":900, "increasechance":0.0, "duration": 10, "modifier": 0.5},
# {"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.25}]}'
EventsJson = os.environ['EVENTS']

#'{"timers": [{"name": "Business Hours", "start":"00:00:00", "end":"07:00:00", "modifier":0.99, "appliedTo": "WHO|WHAT|IDK"}, {"name": "Hour of Darkness", "start":"00:00:00", "end":"08:00:00", "modifier":-0.99, "appliedTo": "TMRW"}]}'
TimersJson = os.environ['TIMERS']

SKIP_EVENT_HUB = True if int(os.environ['SKIPEVENTHUB']) == 1 else False

if SKIP_EVENT_HUB:
    print("Skipping Event Hub - events will not be sent to Event Hub")

# Extended stock info is intended to help show correlation on the data on the backend
# by including events (up or down) in the data feed (stockEvent and marketEvent)
EXTENDED_STOCK_INFO = True if int(os.environ['EXTENDEDSTOCKINFO']) == 1 else False

GROWTH_INCEPTION_DATE = datetime.datetime.strptime("2023-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')

timestamp = datetime.datetime.utcnow()

class StockVariables:
    def __init__(self, stockVariables) -> None:
        self.name = stock["name"]
        self.startPrice = float(stock["startprice"])
        self.minPrice = float(stock["minprice"])
        self.maxPrice = float(stock["maxprice"])
        self.currentPrice = float(stock["startprice"])
        self.mu = float(stock["mu"])
        self.sigma = float(stock["sigma"])
        self.correctionChance = float(stock["correctionchance"])
        self.correctionLength = int(stock["correctionlength"])
        self.correctionCounter = 0
        self.correctionModifier = float(stock["correctionmodifier"])
        self.isInCorrection = False
        self.isCorrectionUpwards = True
        self.aboveStartingCount = 1
        self.belowStartingCount = 1
        self.moveUpCount = 1
        self.moveDownCount = 1
        self.increaseChance_0_20 = float(stock["increasechance0-20"])
        self.increaseChance_20_40 = float(stock["increasechance20-40"])
        self.increaseChance_40_60 = float(stock["increasechance40-60"])
        self.increaseChance_60_80 = float(stock["increasechance60-80"])
        self.increaseChance_80_100 = float(stock["increasechance80-100"])
        self.growthRateAnnual = float(stock["annualgrowthrate"])
        self.growthRateDaily = self.growthRateAnnual / 365
    
    def getMaxPrice(self):
        if USE_GROWTH_RATE and self.growthRateAnnual != 0:
            # get days since inception
            daysSinceInception = (timestamp - GROWTH_INCEPTION_DATE).days
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

# print("WHO: ", WHO_vars)
# print("WHAT: ", WHAT_vars)
# print("IDK: ", IDK_vars)
# print("WHY: ", WHY_vars)
# print("BCUZ: ", BCUZ_vars)
# print("TMRW: ", TMRW_vars)
# print("TDY: ", TDY_vars)
# print("IDGD: ", IDGD_vars)

print("STOCKS JSON: ", StocksJson)
print("Events JSON: ", EventsJson)
print("Timers JSON: ", TimersJson)
print("Growth rate: ", USE_GROWTH_RATE)
print("Warm up hours: ", WARM_UP_HOURS)

dataTable = []
# dataTable = [
#      ['WHO', StockVariables(WHO_vars)] 
#     ,['WHAT', StockVariables(WHAT_vars)] 
#     ,['IDK', StockVariables(IDK_vars)] 
#     ,['WHY', StockVariables(WHY_vars)] 
#     ,['BCUZ', StockVariables(BCUZ_vars)] 
#     ,['TMRW', StockVariables(TMRW_vars)] 
#     ,['TDY', StockVariables(TDY_vars)] 
#     ,['IDGD', StockVariables(IDGD_vars)] 
#     ]

numEvents = 0
numTimers = 0

class MessageType(Enum):
    INFO = 1
    ERROR = 2

def printMsg(message, messageType = MessageType.INFO):
    if (not isWarmup) and (PRINT_ONLY_ERRORS == False) or (PRINT_ONLY_ERRORS and messageType == MessageType.ERROR):
        print(message)

# Load Stocks
try:
    AllStocks = json.loads(StocksJson)
    numStocks = len(AllStocks['stocks'])

    if numStocks > 0:
        for stock in AllStocks['stocks']:
            dataTable.append(StockVariables(stock))
            print(f'Stock: {stock["name"]} {str(stock["startprice"])} {str(stock["minprice"])} {str(stock["maxprice"])} ' \
                f'{str(stock["mu"])} {str(stock["sigma"])} {str(stock["correctionchance"])} {str(stock["correctionlength"])} ' \
                f'{str(stock["correctionmodifier"])} {str(stock["increasechance0-20"])} {str(stock["increasechance20-40"])} ' \
                f'{str(stock["increasechance40-60"])} {str(stock["increasechance60-80"])} {str(stock["increasechance80-100"])} ' \
                f'{str(stock["annualgrowthrate"])}')
        
except Exception as e:
    numStocks = 0
    print("Error parsing JSON, cannot continue without stocks.")
    print(e)
    raise e

# Load Events
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

# Load Timers
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
    totalInitialMarketCap = totalInitialMarketCap + record.startPrice
    
# async def run():
# def run():
#     global isWarmup
#     global timestamp

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

isEvent = False
currentEvent = ""
count = 0
aboveMarketCount = 1
belowMarketCount = 1
errorCount = 0

exitWarmuptimestamp = datetime.datetime.utcnow()

if isWarmup:
    timestamp = datetime.datetime.utcnow() - datetime.timedelta(hours=WARM_UP_HOURS)
    print(f"Starting warm up using timestamp: {timestamp}")

while True:

    if isWarmup:
        timestamp = timestamp + datetime.timedelta(seconds=1)
        if timestamp >= exitWarmuptimestamp:
            isWarmup = False
            timestamp = datetime.datetime.utcnow()
            print(f"Warm up complete, starting real-time data generation")
    else:
        timestamp = datetime.datetime.utcnow()

    event_data_batch = None

    if not SKIP_EVENT_HUB and not isWarmup:
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

        # apply timers
        # modifier is cumulative across all timers
        currentTimerModifier = 0.0
        appliedTimers = 0
        if numTimers > 0:
            for timer in AllTimers['timers']:
                if (timer['start'] <= timestamp.time() <= timer['end'] 
                        and (timer['appliedTo'] == 'all' or record.name in timer['appliedTo'].split('|'))
                        and str(timestamp.weekday()) in timer['days'].split('|')
                        and str(timestamp.month) in timer['months'].split('|')
                        and (timer['dayofmonth'] == 'all' or str(timestamp.day) in timer['dayofmonth'].split('|'))
                        ):
                    currentTimerModifier += timer['modifier']
                    appliedTimers += 1

        # priceIncDec = abs(record.currentPrice - (random.normalvariate(record.mu, record.sigma) * record.currentPrice))
        priceIncDec = abs(round(random.normalvariate(record.mu, record.sigma),2))

        priceIncrease = random.random() < record.getIncreaseChance(currentTimerModifier)

        if isEvent:
            if currentEvent['durationCount'] <= 0:
                isEvent = False
            else:
                priceIncrease = currentEvent['isIncreasing'] # force direction if in correction
                priceIncDec = priceIncDec * currentEvent['modifier'] # make corrections more gradual
            record.isInCorrection = False # force individual corrections off if event

        else:
            if record.isInCorrection == False and random.random() < record.correctionChance:
                record.isInCorrection = True
                record.correctionCounter = record.correctionLength
                record.isCorrectionUpwards = random.random() < record.getIncreaseChance(currentTimerModifier)
                printMsg(f'{record.name} Correction ({"UP" if record.isCorrectionUpwards else "DOWN"})')

        if record.isInCorrection:
            if record.correctionCounter <= 0:
                record.isInCorrection = False
            else:
                priceIncrease = record.isCorrectionUpwards # force direction if in correction
                priceIncDec = priceIncDec * record.correctionModifier # make corrections more gradual
                record.correctionCounter -= 1

        if priceIncrease:
            newPrice = round(record.currentPrice + priceIncDec,2)
            # newPrice = (newPrice if newPrice < record.maxPrice else record.maxPrice)
            newPrice = round(newPrice if newPrice < record.getMaxPrice() else record.getMaxPrice(),2)
            record.moveUpCount += 1
            #increase
        else:
            newPrice = round(record.currentPrice - priceIncDec,2)
            newPrice = (newPrice if newPrice > record.minPrice else record.minPrice)
            record.moveDownCount += 1
            #decrease

        record.currentPrice = newPrice
        if (record.currentPrice > record.startPrice):
            record.aboveStartingCount += 1
        else:
            record.belowStartingCount += 1
                
        extendedStockValue = 0 
        if record.isInCorrection:
            extendedStockValue = 1 if record.isCorrectionUpwards else -1

        extendedMarketValue = 0
        if isEvent:
            extendedMarketValue = 1 if currentEvent['isIncreasing'] else -1

        if EXTENDED_STOCK_INFO:
            reading = {'symbol': record.name, 'price': newPrice, 'timestamp': str(timestamp), 
                        'stockEvent': extendedStockValue,
                        'marketEvent': extendedMarketValue,
                        'timer': appliedTimers #1 if isTimer else 0
                        }
        else:
            reading = {'symbol': record.name, 'price': newPrice, 'timestamp': str(timestamp)}

        s = json.dumps(reading)

        printMsg(s + 
                f' O/U:{record.aboveStartingCount/record.belowStartingCount:.2f} ' + 
                f'| U/D:{record.moveUpCount/record.moveDownCount:.2f} ' +
                f'| R:{record.getPriceRange():.2f} ' +
                f'| IC:{record.getIncreaseChance(currentTimerModifier):.4f} ' + 
                f'| T:{appliedTimers} ' +
                f'| M:{extendedMarketValue} ' +
                f'| S:{extendedStockValue}')

        if not SKIP_EVENT_HUB and not isWarmup:
            try:
                if not event_data_batch is None: 
                    event_data_batch.add(EventData(s)) # add event data to the batch
            except Exception as e:
                errorCount += 1
                printMsg(f"{datetime.datetime.utcnow()} Error adding to batch ({errorCount}) - {e}", MessageType.ERROR)

        totalMarketCap = totalMarketCap + newPrice

    if not SKIP_EVENT_HUB and not isWarmup:
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
    
    if not isWarmup:
        time.sleep(1)
        
# asyncio.run(run())
# run()