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
ENV WHO_vars "600|1|1200|1|0.04|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV WHAT_vars "600|1|1200|1|0.04|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV IDK_vars "600|1|1200|1|0.04|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV WHY_vars "600|1|1200|1|0.04|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV BCUZ_vars "600|1|1200|1|0.04|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV TMRW_vars "600|1|1200|1|0.04|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV TDY_vars "600|1|1200|1|0.05|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"
ENV IDGD_vars "600|1|1200|1|0.05|0.004|30|0.4|0.600|0.557|0.557|0.557|0.490"

ENV EVENTS '{"events": [{"type": "periodic", "name": "300-up", "frequency":300, "increasechance":1.0, "duration": 5, "modifier": 0.5},{"type": "periodic", "name": "900-down", "frequency":900, "increasechance":0.0, "duration": 10, "modifier": 0.5},{"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.25}]}'

ENV EXTENDEDSTOCKINFO=0

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
