FROM python:3.10-alpine

WORKDIR /app

# copy the requirements file in the workdir
COPY requirements.txt /app

# install the Python requirements
RUN pip install -r requirements.txt

# copy the app files and directories
COPY .. /app/

# start booking.py when the container is started
CMD ["python","-u","booking.py"]