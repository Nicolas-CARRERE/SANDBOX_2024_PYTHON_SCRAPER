FROM python:3.10

# Install Java
RUN apt update && \
  apt install -y sudo && \
  sudo apt install default-jdk -y

## Pip dependencies
# Upgrade pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Install production dependencies
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
  rm /tmp/requirements.txt
# Install development dependencies
# COPY ../requirements-dev.txt /tmp/requirements-dev.txt
# RUN pip install -r /tmp/requirements-dev.txt && \
#   rm /tmp/requirements-dev.txt