FROM ubuntu:18.04

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    mkdir /root/.conda && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \
    rm -f Miniconda3-latest-Linux-x86_64.sh

ENV PATH="/opt/miniconda3/bin:${PATH}"

RUN conda config --add channels conda-forge && \
    conda config --add channels terradue && \
    conda config --add channels anaconda && \
    conda config --add channels edeno

COPY spike_interface_0_97_1.yml .

RUN conda env create -f spike_interface_0_97_1.yml

SHELL ["conda", "run", "-n", "spike_interface_0_97_1", "/bin/bash", "-c"]

COPY . .

CMD ["python", "app.py"]