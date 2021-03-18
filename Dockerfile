FROM python:3.7

COPY . /app
WORKDIR /app

RUN pip install -e .

CMD ["/bin/bash"]