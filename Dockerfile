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
# ENV WHO_vars "300|1|1400|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
# ENV WHAT_vars "300|2|950|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
# ENV IDK_vars "300|3|1300|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
# ENV WHY_vars "300|4|1100|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
# ENV BCUZ_vars "300|5|1000|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"
# ENV TMRW_vars "300|6|1050|1|0.04|0.004|30|0.4|0.590|0.550|0.550|0.510|0.480"
# ENV TDY_vars "300|7|1500|1|0.04|0.004|30|0.4|0.590|0.550|0.550|0.510|0.480"
# ENV IDGD_vars "300|8|1200|1|0.04|0.004|30|0.4|0.570|0.550|0.550|0.510|0.480"

ENV WHO_vars="600|100|1400|.04|0.9|0.01|60|0.4|0.510|0.505|0.500|0.484|0.442"
ENV WHAT_vars="500|50|1250|.04|0.8|0.01|60|0.4|0.510|0.502|0.500|0.481|0.442"
ENV IDK_vars="500|100|1200|.04|0.9|0.01|60|0.4|0.535|0.540|0.520|0.500|0.475"
ENV WHY_vars="550|50|1300|.04|0.9|0.01|60|0.4|0.515|0.515|0.503|0.480|0.442"
ENV BCUZ_vars="300|10|750|.03|0.7|0.01|60|0.4|0.530|0.532|0.535|0.500|0.465"
ENV TMRW_vars="500|50|1300|.07|1.0|0.01|60|0.4|0.530|0.530|0.520|0.502|0.425"
ENV TDY_vars="700|300|1500|.07|1.0|0.01|60|0.4|0.530|0.530|0.520|0.502|0.425"
ENV IDGD_vars="500|50|1150|.04|0.8|0.01|60|0.4|0.503|0.500|0.496|0.492|0.451"

#ENV EVENTS '{"events": [{"type": "periodic", "name": "300-up", "frequency":300, "increasechance":1.0, "duration": 5, "modifier": 0.5},{"type": "periodic", "name": "900-down", "frequency":900, "increasechance":0.0, "duration": 10, "modifier": 0.5},{"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.25}]}'
#ENV TIMERS '{"timers": [{"name": "Business Hours", "start":"09:00:00", "end":"17:00:00", "modifier":0.02, "appliedTo": "WHO|WHAT|WHY"}]}'
ENV EVENTS='{"events": [{"type": "periodic", "name": "900-up", "frequency":900, "increasechance":1.0, "duration": 60, "modifier": 0.5},{"type": "periodic", "name": "5220-down", "frequency":5220, "increasechance":0.0, "duration": 30, "modifier": 0.5},{"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.4}]}'

#ENV TIMERS '{"timers": [{"name": "ET Business Hours", "start":"14:00:00", "end":"22:00:00", "modifier":0.02, "appliedTo": "WHO|WHAT|WHY"}, {"name": "GMT Business Hours", "start":"08:00:00", "end":"17:00:00", "modifier":0.02, "appliedTo": "TMRW|TDY"}, {"name": "Hour of Darkness", "start":"00:00:00", "end":"01:00:00", "modifier":-0.05, "appliedTo": "IDGD"}]}'
ENV TIMERS='{"timers": [{"name": "Workdays", "start":"08:00:00", "end":"18:00:00", "days":"0|1|2|3|4", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.0004, "appliedTo": "WHO|WHAT|IDK|WHY|BCUZ|TMRW|TDY|IDGD"}, {"name": "Evening Decline", "start":"22:00:00", "end":"23:59:59", "days":"0|1|2|3|4|5|6", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.03, "appliedTo": "WHO|WHAT|IDK|WHY|BCUZ|TMRW|TDY|IDGD"}, {"name": "Morning Rise", "start":"04:00:00", "end":"06:00:00", "days":"0|1|2|3|4|5|6", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.0003, "appliedTo": "WHO|WHAT|IDK|WHY|BCUZ|TMRW|TDY|IDGD"}, {"name": "ET Business Hours", "start":"14:00:00", "end":"22:00:00", "days":"0|2|4", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.04, "appliedTo": "WHO|WHAT|WHY"}, {"name": "WHO Fridays", "start":"14:00:00", "end":"22:00:00", "days":"4", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.06, "appliedTo": "WHO"}, {"name": "GMT Business Hours", "start":"08:00:00", "end":"17:00:00", "days":"0|1|2|3|4", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.02, "appliedTo": "TMRW|TDY"}, {"name": "Lunch Slump", "start":"12:00:00", "end":"13:00:00", "days":"0|1|2|3|4", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.01, "appliedTo": "WHO|WHAT|IDK|WHY|BCUZ|TMRW|TDY|IDGD"}, {"name": "Hour of Darkness", "start":"01:00:00", "end":"02:00:00", "days":"0|1|2|3|4|5|6", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.055, "appliedTo": "IDGD"}, {"name": "Happy Wednesdays", "start":"01:00:00", "end":"23:00:00", "days":"2", "months": "1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.035, "appliedTo": "IDGD"}]}'

ENV EXTENDEDSTOCKINFO=0
ENV SKIPEVENTHUB=0
ENV PRINTONLYERRORS=0

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
