FROM python:3

ARG appname=leopard_lavatory

WORKDIR /${appname}

COPY requirements.txt /${appname}/
COPY dist/${appname}*.tar.gz /${appname}/

RUN pip install -r requirements.txt
RUN pip install ${appname}*

CMD ["python", \
     "-m", \
     "leopard_lavatory.run"]