# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV EVENTHUBCONNECTIONSTRING "Endpoint=sb://abc123.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=abc123"
ENV EVENTHUBNAME "stockeventhub"
ENV EVENTHUBFQNS "ehns-123456-stockevents.servicebus.windows.net"
ENV USEMANAGEDIDENTITY=0

# stock variables: 
# start price | min price | max price | mu | sigma | correction chance | correction length | correction modifier

# last five:
# 0-20 increase chance | 20-40 increase chance | 40-60 increase chance | 60-80 increase chance | 80-100 increase chance

# ENV WHO_vars="600|100|1400|.04|0.9|0.01|60|0.4|0.510|0.505|0.500|0.484|0.442"
# ENV WHAT_vars="500|50|1250|.04|0.8|0.01|60|0.4|0.510|0.502|0.500|0.481|0.442"
# ENV IDK_vars="500|100|1200|.04|0.9|0.01|60|0.4|0.535|0.540|0.520|0.500|0.475"
# ENV WHY_vars="550|50|1300|.04|0.9|0.01|60|0.4|0.515|0.515|0.503|0.480|0.442"
# ENV BCUZ_vars="300|10|950|.03|0.7|0.01|60|0.4|0.520|0.510|0.505|0.500|0.465"
# ENV TMRW_vars="500|50|1300|.07|1.0|0.01|60|0.4|0.530|0.520|0.515|0.502|0.430"
# ENV TDY_vars="700|225|1500|.07|1.0|0.01|60|0.4|0.530|0.520|0.515|0.502|0.430"
# ENV IDGD_vars="500|50|1150|.04|0.8|0.01|60|0.4|0.503|0.500|0.496|0.492|0.451"

# last:
# annual growth rate

ENV WHO_vars="600|100|1200|.04|0.9|0.01|60|0.4|0.510|0.505|0.500|0.484|0.442|0.08"
ENV WHAT_vars="500|50|1050|.04|0.8|0.01|60|0.4|0.510|0.502|0.500|0.481|0.442|0.07"
ENV IDK_vars="500|100|1100|.04|0.9|0.01|60|0.4|0.535|0.540|0.520|0.500|0.475|0.065"
ENV WHY_vars="550|25|1200|.04|0.9|0.01|60|0.4|0.515|0.515|0.503|0.480|0.442|-0.02"
ENV BCUZ_vars="300|5|950|.03|0.7|0.01|60|0.4|0.520|0.510|0.505|0.500|0.465|0.06"
ENV TMRW_vars="500|50|1100|.07|1.0|0.01|60|0.4|0.530|0.520|0.515|0.502|0.430|0.052"
ENV TDY_vars="700|225|1250|.07|1.0|0.01|60|0.4|0.530|0.520|0.515|0.502|0.430|0.02"
ENV IDGD_vars="500|50|1050|.04|0.8|0.01|60|0.4|0.503|0.500|0.496|0.492|0.451|0.055"

ENV STOCKS='{"stocks": [{"name":"WHO","startprice":600,"minprice":100,"maxprice":1200,"mu":0.04,"sigma":0.9,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.510,"increasechance20-40":0.505,"increasechance40-60":0.500,"increasechance60-80":0.484,"increasechance80-100":0.442,"annualgrowthrate":0.08},{"name":"WHAT","startprice":500,"minprice":50,"maxprice":1050,"mu":0.04,"sigma":0.8,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.510,"increasechance20-40":0.502,"increasechance40-60":0.500,"increasechance60-80":0.481,"increasechance80-100":0.442,"annualgrowthrate":0.07},{"name":"IDK","startprice":500,"minprice":100,"maxprice":1100,"mu":0.04,"sigma":0.9,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.535,"increasechance20-40":0.540,"increasechance40-60":0.520,"increasechance60-80":0.500,"increasechance80-100":0.475,"annualgrowthrate":0.065},{"name":"WHY","startprice":550,"minprice":25,"maxprice":1200,"mu":0.04,"sigma":0.9,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.515,"increasechance20-40":0.515,"increasechance40-60":0.503,"increasechance60-80":0.480,"increasechance80-100":0.442,"annualgrowthrate":-0.02},{"name":"BCUZ","startprice":300,"minprice":5,"maxprice":950,"mu":0.03,"sigma":0.7,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.520,"increasechance20-40":0.510,"increasechance40-60":0.505,"increasechance60-80":0.500,"increasechance80-100":0.465,"annualgrowthrate":0.06},{"name":"TMRW","startprice":500,"minprice":50,"maxprice":1100,"mu":0.07,"sigma":1.0,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.530,"increasechance20-40":0.520,"increasechance40-60":0.515,"increasechance60-80":0.502,"increasechance80-100":0.430,"annualgrowthrate":0.052},{"name":"TDY","startprice":700,"minprice":225,"maxprice":1250,"mu":0.07,"sigma":1.0,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.530,"increasechance20-40":0.520,"increasechance40-60":0.515,"increasechance60-80":0.502,"increasechance80-100":0.430,"annualgrowthrate":0.02},{"name":"IDGD","startprice":500,"minprice":50,"maxprice":1050,"mu":0.04,"sigma":0.8,"correctionchance":0.01,"correctionlength":60,"correctionmodifier":0.4,"increasechance0-20":0.503,"increasechance20-40":0.500,"increasechance40-60":0.496,"increasechance60-80":0.492,"increasechance80-100":0.451,"annualgrowthrate":0.055}]}'

ENV EVENTS='{"events": [{"type": "periodic", "name": "900-up", "frequency":900, "increasechance":1.0, "duration": 60, "modifier": 0.5},{"type": "periodic", "name": "5220-down", "frequency":5220, "increasechance":0.0, "duration": 30, "modifier": 0.5},{"type": "random", "name": "Rando1", "frequency": 0.003, "increasechance": 0.504, "duration": 30, "modifier": 0.4}]}'

ENV TIMERS='{"timers": [{"name": "Workdays", "start":"08:00:00", "end":"18:00:00", "days":"0|1|2|3|4", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.0004, "appliedTo": "WHO|WHAT|IDK|WHY|BCUZ|TMRW|TDY|IDGD"}, {"name": "Evening Decline", "start":"22:00:00", "end":"23:59:59", "days":"0|1|2|3|4|5|6", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.03, "appliedTo": "WHO|WHAT|IDK|WHY|IDGD"}, {"name": "Morning Rise", "start":"04:00:00", "end":"06:00:00", "days":"0|1|2|3|4|5|6", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.0003, "appliedTo": "WHO|WHAT|IDK|WHY|BCUZ|TMRW|TDY|IDGD"}, {"name": "ET Business Hours MWF", "start":"14:00:00", "end":"22:00:00", "days":"0|2|4", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.04, "appliedTo": "WHO|WHAT|WHY"}, {"name": "WHO Fridays", "start":"14:00:00", "end":"22:00:00", "days":"4", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.06, "appliedTo": "WHO"}, {"name": "GMT Business Hours M-F", "start":"08:00:00", "end":"17:00:00", "days":"0|1|2|3|4", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.015, "appliedTo": "TMRW|TDY"},  {"name": "Weekend Slide", "start":"00:00:00", "end":"23:59:59", "days":"5|6", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.012, "appliedTo": "TMRW|TDY"}, {"name": "GMT Business Hours M", "start":"07:00:00", "end":"18:00:00", "days":"0", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.025, "appliedTo": "TMRW|TDY"}, {"name": "Lunch Slump", "start":"12:00:00", "end":"13:00:00", "days":"0|1|2|3|4", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.01, "appliedTo": "WHO|WHAT|IDK|WHY|IDGD"}, {"name": "Hour of Darkness", "start":"01:00:00", "end":"02:00:00", "days":"0|1|2|3|4|5|6", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":-0.055, "appliedTo": "IDGD"}, {"name": "Happy Wednesdays", "start":"01:00:00", "end":"23:00:00", "days":"2", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.035, "appliedTo": "IDGD"}, {"name": "BCUZ Weekends", "start":"00:00:00", "end":"23:59:59", "days":"5|6", "dayofmonth":"all", "months":"1|2|3|4|5|6|7|8|9|10|11|12", "modifier":0.026, "appliedTo": "BCUZ"}]}'

ENV USEGROWTHRATE=1
ENV EXTENDEDSTOCKINFO=0
ENV SKIPEVENTHUB=1
ENV PRINTONLYERRORS=0
ENV WARMUPHOURS=0

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
