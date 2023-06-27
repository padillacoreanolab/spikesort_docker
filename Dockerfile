FROM ubuntu:18.04

RUN apt-get update && apt-get install -y wget bzip2

RUN wget https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh && \
    chmod +x Anaconda3-2021.11-Linux-x86_64.sh && \
    ./Anaconda3-2021.11-Linux-x86_64.sh -b -p /opt/anaconda3 && \
    rm Anaconda3-2021.11-Linux-x86_64.sh

ENV PATH="/opt/anaconda3/bin:${PATH}"

COPY requirements.yml .

RUN conda env create -f requirements.yml

SHELL ["conda", "run", "-n", "spike_interface_0_97_1", "/bin/bash", "-c"]

COPY . .

CMD ["python", "app.py"]