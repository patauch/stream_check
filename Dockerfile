FROM python:3.9.10

## Pip dependencies
# Upgrade pip
RUN pip install --upgrade pip
# Copy dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


