FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.7-minimal python3.7-venv \
    git cmake make libssl-dev wget g++-11 iproute2
RUN ln -sf /usr/bin/g++-11 /usr/bin/g++ & ln -sf /usr/bin/g++ /usr/bin/c++

RUN wget https://archives.boost.io/release/1.76.0/source/boost_1_76_0.tar.bz2
RUN tar xjf boost_1_76_0.tar.bz2
WORKDIR /workspace/boost_1_76_0
RUN ./bootstrap.sh --prefix=/usr/local --with-libraries=context,fiber,filesystem,log,system,thread,program_options,json
RUN ./b2 install variant=release link=static,shared threading=multi -j 4 define=BOOST_LOG_USE_NATIVE_SYSLOG define=BOOST_ERROR_CODE_HEADER_ONLY
WORKDIR /workspace
RUN rm -r boost_1_76_0 boost_1_76_0.tar.bz2
ENV LD_LIBRARY_PATH="/usr/local/lib"

RUN git config --global http.sslVerify false 

RUN git clone --recursive --config core.autocrlf=input https://github.com/encryptogroup/MOTION.git

WORKDIR /workspace/MOTION
ADD motion.patch .
RUN git apply motion.patch
RUN cmake -S . -B build -DMOTION_BUILD_EXE=On
RUN cmake --build build --parallel

WORKDIR /workspace

RUN git config --global http.sslVerify true

RUN python3.7 -m venv /workspace/venv
ENV PATH="/workspace/venv/bin:${PATH}"
RUN pip install --upgrade pip && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install omegaconf onnx pandas pyyaml tensorboard future scipy scikit-learn && \
    pip install crypten --no-deps