# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV increasechance 0.502
ENV sigma 0.05
ENV mu 1
ENV stockstartprice 100
ENV stockceiling 1200
ENV stockfloor 1
ENV marketcorrectionchance 0.002
ENV marketcorrectionlength 60
ENV marketcorrectionmodifier 0.7
ENV individualcorrectionchance 0.005
ENV individualcorrectionlength 30
ENV individualcorrectionmodifier 0.4

ENV eventconnectionstring "Endpoint=sb://<<NAME>>.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=<<KEY>>"
ENV eventhubname "fwtheventhub"

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
