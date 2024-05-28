################### Build cvc5
FROM satcomp-infrastructure:common
USER root
#  Install required softwares
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt install -y cmake build-essential zlib1g-dev libopenmpi-dev wget unzip build-essential zlib1g-dev cmake python3.8 build-essential gfortran wget curl default-jre python3.8-tk flex bison python3.8-venv

# Build cvc5
RUN /usr/bin/python3.8 -m pip install toml
RUN /usr/bin/python3.8 -m pip install tomli
RUN /usr/bin/python3.8 -m pip install pyparsing
RUN /usr/bin/python3.8 -m pip install mpi4py

RUN git clone https://github.com/SMT-COMP/scrambler.git
WORKDIR scrambler
RUN git fetch
RUN git pull
RUN make scrambler

WORKDIR /
RUN git clone https://github.com/cvc5/cvc5.git
WORKDIR cvc5
RUN git fetch
RUN git pull
RUN git checkout main
RUN ./configure.sh --auto-download --static --static-binary
RUN cd build && make -j8 && cd ..