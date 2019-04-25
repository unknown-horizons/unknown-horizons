FROM ubuntu:18.04

# docker build -f development/docker/Dockerfile -t unknown-horizons .

RUN apt-get update && \
    apt-get install -y build-essential \
                       libalsa-ocaml-dev \
                       libsdl2-dev \
                       libboost-dev \ 
                       libsdl2-ttf-dev \
                       libsdl2-image-dev \
                       libvorbis-dev \
                       libalut-dev \
                       python3 \
                       python3-dev \
                       libboost-regex-dev \
                       libboost-filesystem-dev \
                       libboost-test-dev \
                       swig \
                       zlib1g-dev \
                       libopenal-dev \
                       git \
                       python3-yaml \
                       libxcursor1 \
                       libxcursor-dev \
                       cmake \
                       cmake-data \
                       libtinyxml-dev \
                       libpng-dev \
                       libglew-dev \
                       python3-enet \
                       intltool \
                       python3-pillow \
                       python3-future

# Install Fifengine and Fifechan
RUN git clone https://github.com/fifengine/fifechan.git && \
    cd fifechan && \
    mkdir _build && \
    cd _build && \
    cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr .. && \
    make && make install

RUN git clone https://github.com/fifengine/fifengine.git && \
    cd fifengine && \
    mkdir _build && \
    cd _build && \
    cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DPYTHON_EXECUTABLE=/usr/bin/python3 .. && \
    make && make install

RUN mkdir -p /code
ADD . /code
WORKDIR /code
RUN python3 setup.py build_i18n && \
    adduser --disabled-password --gecos "" horizonuser
RUN usermod -a -G video horizonuser
USER horizonuser
RUN mkdir -p ~/.config/unknown-horizons/ && \
    cp content/settings-template.xml ~/.config/unknown-horizons/settings.xml

# Also create config for root user that can leverage video
USER root
RUN mkdir -p ~/.config/unknown-horizons/ && \
    cp content/settings-template.xml ~/.config/unknown-horizons/settings.xml

ENTRYPOINT ["python3", "/code/run_uh.py"]
