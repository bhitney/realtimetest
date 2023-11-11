# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV EVENTHUBCONNECTIONSTRING "Endpoint=sb://abc123.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=abc123"
ENV EVENTHUBNAME "fwtheventhub"

# stock variables: 
# start price | min price | max price | mu | sigma | correction chance | correction length | correction modifier

# last five:
# 0-20 increase chance | 20-40 increase chance | 40-60 increase chance | 60-80 increase chance | 80-100 increase chance

# default values: "600|1|1200|1|0.04|0.004|30|0.4|0.557|0.557|0.557|0.557|0.557"
ENV WHO_vars "300|1|1400|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
ENV WHAT_vars "300|2|950|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
ENV IDK_vars "300|3|1300|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
ENV WHY_vars "300|4|1100|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
ENV BCUZ_vars "300|5|1000|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
ENV TMRW_vars "300|6|1050|1|0.04|0.004|30|0.4|0.590|0.550|0.550|0.510|0.480"
ENV TDY_vars "300|7|1500|1|0.04|0.004|30|0.4|0.590|0.550|0.550|0.510|0.480"
ENV IDGD_vars "300|8|1200|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"

ENV EVENTS '{"events": [{"type": "periodic", "name": "300-up", "frequency":300, "increasechance":1.0, "duration": 5, "modifier": 0.5},{"type": "periodic", "name": "900-down", "frequency":900, "increasechance":0.0, "duration": 10, "modifier": 0.5},{"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.25}]}'
#ENV TIMERS '{"timers": [{"name": "Business Hours", "start":"09:00:00", "end":"17:00:00", "modifier":0.02, "appliedTo": "WHO|WHAT|WHY"}]}'

ENV TIMERS '{"timers": [{"name": "ET Business Hours", "start":"14:00:00", "end":"22:00:00", "modifier":0.02, "appliedTo": "WHO|WHAT|WHY"}, {"name": "GMT Business Hours", "start":"08:00:00", "end":"17:00:00", "modifier":0.02, "appliedTo": "TMRW|TDY"}, {"name": "Hour of Darkness", "start":"00:00:00", "end":"01:00:00", "modifier":-0.05, "appliedTo": "IDGD"}]}'

ENV EXTENDEDSTOCKINFO=0
ENV SKIPEVENTHUB=0

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "main.py"]
