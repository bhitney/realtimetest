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

EVENT_HUB_CONNECTION_STR = os.environ['eventconnectionstring']
EVENT_HUB_NAME = os.environ['eventhubname']

Mu = float(os.environ['mu']) 
Sigma = float(os.environ['sigma']) 
IncreaseChance = float(os.environ['increasechance']) 
StockStartPrice = float(os.environ['stockstartprice']) 

MarketCorrectionChance = float(os.environ['marketcorrectionchance']) 
MarketCorrectionLength = float(os.environ['marketcorrectionlength']) 
MarketCorrectionModifier = float(os.environ['marketcorrectionmodifier']) 

IndividualCorrectionChance = float(os.environ['individualcorrectionchance']) 
IndividualCorrectionLength = float(os.environ['individualcorrectionlength']) 
IndividualCorrectionModifier = float(os.environ['individualcorrectionmodifier']) 

StockFloor = float(os.environ['stockfloor']) 
StockCeiling = float(os.environ['stockceiling']) 

print("Mu: " + str(Mu))
print("Sigma: " + str(Sigma))
print("Increasing Chance: " + str(IncreaseChance))
print("StockStartPrice: " + str(StockStartPrice))
print("EventHub: " + EVENT_HUB_NAME)
print("EventHubConnString: " + EVENT_HUB_CONNECTION_STR)

# symbol, starting prince, in stock correction, correction length, correction upwards
dataTable = [
     ['WHO', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['WHAT', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['IDK', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['WHY', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['BCUZ', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['TMRW', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['TDY', StockStartPrice, False, IndividualCorrectionLength, True] 
    ,['IDGD', StockStartPrice, False, IndividualCorrectionLength, True] 
    ]

async def run():
    # Create a producer client to send messages to the event hub.
    # Specify a connection string to your event hubs namespace and
    # the event hub name.
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENT_HUB_CONNECTION_STR, eventhub_name=EVENT_HUB_NAME
    )

    async with producer:

        isMarketCorrection = False # track fake stock market correction
        currentCorrectionCount = MarketCorrectionLength
        correctionUpward = False
        count = 0

        while True:
            
            timestamp = str(datetime.datetime.utcnow())
            event_data_batch = await producer.create_batch() # create a batch

            if isMarketCorrection == False and random.random() < MarketCorrectionChance:
                    isMarketCorrection = True
                    currentCorrectionCount = MarketCorrectionLength
                    correctionUpward = random.random() < IncreaseChance
                    print("Market Correction (" + ("UP" if correctionUpward else "DOWN") + ")")

            totalMarketCap = 0

            for record in dataTable:    
                symbol = record[0]
                price = record[1]
                stockCorrection = record[2]
                stockCorrectionLength = record[3]
                stockCorrectionIncrease = record[4]

                priceIncDec = abs(price - (random.normalvariate(Mu, Sigma) * price))
                priceIncrease = random.random() < IncreaseChance
 
                if isMarketCorrection:
                    if currentCorrectionCount <= 0:
                        isMarketCorrection = False
                    else:
                        priceIncrease = correctionUpward # force direction if in correction
                        priceIncDec = priceIncDec * MarketCorrectionModifier # make corrections more gradual
                else:
                    if stockCorrection == False and random.random() < IndividualCorrectionChance:
                        stockCorrection = True
                        stockCorrectionLength = IndividualCorrectionLength
                        stockCorrectionIncrease = random.random() < IncreaseChance
                        print(symbol + " Correction (" + ("UP" if stockCorrectionIncrease else "DOWN") + ")")

                if stockCorrection:
                    if stockCorrectionLength <= 0:
                        stockCorrection = False
                    else:
                        priceIncrease = stockCorrectionIncrease # force direction if in correction
                        priceIncDec = priceIncDec * IndividualCorrectionModifier # make corrections more gradual
                        stockCorrectionLength = stockCorrectionLength - 1

                if priceIncrease:
                    newPrice = math.ceil(price + priceIncDec)
                    newPrice = (newPrice if newPrice < StockCeiling else StockCeiling)
                    #increase
                else:
                    newPrice = math.floor(price - priceIncDec)
                    newPrice = (newPrice if newPrice > StockFloor else StockFloor)
                    #decrease

                record[1] = newPrice
                record[2] = stockCorrection
                record[3] = stockCorrectionLength
                record[4] = stockCorrectionIncrease
                 
                reading = {'symbol': symbol, 'price': newPrice, 'timestamp': timestamp}
                s = json.dumps(reading)
                print(s)

                event_data_batch.add(EventData(s)) # add event data to the batch

                totalMarketCap = totalMarketCap + newPrice

            # send the batch of events to the event hub
            await producer.send_batch(event_data_batch)

            if isMarketCorrection:
                currentCorrectionCount = currentCorrectionCount - 1

            count = count + 1
            print(str(count) + ": Total Market Cap: " + str(totalMarketCap))
         
            time.sleep(1)

asyncio.run(run())    