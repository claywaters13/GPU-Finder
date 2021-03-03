FROM python:3.7-alpine
RUN pip3 install requests
RUN pip3 install bs4
RUN pip3 install twilio
WORKDIR /usr/src/app
COPY . .
CMD ["main.py"]
ENTRYPOINT ["python3"]
