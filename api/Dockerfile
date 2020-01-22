# Use the Python3.6.9 image
FROM python:3.6.9-stretch

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# for dryscrape ... install webkit-server from git and xvfb
# RUN cd webkit-server && python setup.py install && apt-get update && apt-get install -y xvfb
RUN  apt-get update && apt-get install -y xvfb qt5-default libqt5webkit5-dev build-essential python-lxml python-pip xvfb

# Install the dependencies
RUN pip install -r requirements.txt

# Run the command to start gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:9003", "-t 90"]
