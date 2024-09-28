FROM python:3.10

# Install Java
RUN apt update && \
  apt install -y sudo default-jdk

# Upgrade pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Create a virtual environment
RUN python -m venv /opt/venv

# Install production dependencies
COPY ./requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt && \
  rm /tmp/requirements.txt

# The following lines can be used if you have development dependencies
# COPY ../requirements-dev.txt /tmp/requirements-dev.txt
# RUN /opt/venv/bin/pip install -r /tmp/requirements-dev.txt && \
#   rm /tmp/requirements-dev.txt

# Set the virtual environment as the default python
ENV PATH="/opt/venv/bin:$PATH"
