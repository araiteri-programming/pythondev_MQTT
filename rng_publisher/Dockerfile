FROM python:latest
RUN mkdir /python_files
COPY . /python_files
RUN chmod -R 777 /python_files
RUN ls -l /python_files
RUN pip install -r /python_files/requirements.txt
WORKDIR /python_files
CMD tail -f /dev/null