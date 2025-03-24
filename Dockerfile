FROM ubuntu:20.04

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    apt-get install -y wget build-essential git && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    mkdir /root/.conda && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \
    rm -f Miniconda3-latest-Linux-x86_64.sh

ENV PATH="/root/miniconda3/bin:${PATH}"

RUN conda create -n spikesort python=3.12 --yes
# activate conda env
SHELL ["conda", "run", "-n", "spikesort", "/bin/bash", "-c"]
RUN pip install spikeinterface[full,widgets]==0.102.1
RUN pip install kilosort==4.0.30

RUN conda init bash
RUN echo ". ~/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc

# copy all files in the directory over to container
COPY . .

# CMD ["conda", "run", "-n", "spikesort", "python", "app.py"]