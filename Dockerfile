FROM ubuntu:20.04

ARG UID=1000
ARG GID=1000
ARG TZ=Europe/Zurich

ARG ILASTIK_BINARY=ilastik-1.3.3post3-Linux.tar.bz2
ARG CELLPROFILER_VERSION=v4.1.3
ARG CELLPROFILER_PLUGINS_VERSION=v4.2.1

RUN apt-get update && apt-get install -y ca-certificates locales wget git build-essential python3-pip
RUN echo "deb mirror://mirrors.ubuntu.com/mirrors.txt focal main restricted universe multiverse " > /etc/apt/sources.list && \
    echo "deb mirror://mirrors.ubuntu.com/mirrors.txt focal-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb mirror://mirrors.ubuntu.com/mirrors.txt focal-security main restricted universe multiverse" >> /etc/apt/sources.list

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US:en" \
    LC_ALL="en_US.UTF-8"

RUN ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && echo "${TZ}" > /etc/timezone

ENV PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1"

RUN addgroup --gid "${GID}" steinbock && \
    adduser --uid "${UID}" --gid "${GID}" --disabled-password --gecos "" steinbock && \
    mkdir /data && chown steinbock:steinbock /data

# ilastik

RUN wget -q "https://files.ilastik.org/${ILASTIK_BINARY}" && \
    mkdir /opt/ilastik && \
    tar -xjf "${ILASTIK_BINARY}" -C /opt/ilastik --strip-components=1 && \
    rm "${ILASTIK_BINARY}"

# cellprofiler

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    default-libmysqlclient-dev \
    libgtk-3-dev \
    libnotify-dev \
    libsdl2-dev \
    openjdk-11-jdk-headless
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"

RUN wget -q https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    pip3 install --upgrade numpy wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    rm wxPython-4.1.0-cp38-cp38-linux_x86_64.whl

RUN git clone -b "${CELLPROFILER_VERSION}" --depth 1 https://github.com/CellProfiler/CellProfiler.git && \
    pip3 install --upgrade --prefix=/usr/local ./CellProfiler && \
    rm -r CellProfiler

# cellprofiler plugins

RUN git clone -b "${CELLPROFILER_PLUGINS_VERSION}" https://github.com/BodenmillerGroup/ImcPluginsCP.git && \
    cp -r ImcPluginsCP/plugins /opt/cellprofiler_plugins && \
    rm -r ImcPluginsCP

# steinbock

COPY ./requirements.txt .
RUN pip3 install --upgrade deepcell==0.9.0 && \
    pip3 install --upgrade -r requirements.txt && \
    rm requirements.txt
ENV TF_CPP_MIN_LOG_LEVEL="2" \
    NO_AT_BRIDGE="1"

RUN wget -q https://deepcell-data.s3-us-west-1.amazonaws.com/saved-models/MultiplexSegmentation-7.tar.gz && \
    mkdir -p /home/steinbock/.keras/models && \
    tar -xzf MultiplexSegmentation-7.tar.gz -C /home/steinbock/.keras/models && \
    rm /home/steinbock/.keras/models/._MultiplexSegmentation && \
    chown -R steinbock:steinbock /home/steinbock/.keras && \
    rm MultiplexSegmentation-7.tar.gz

RUN mkdir /app
COPY . /app/steinbock
RUN pip3 install --upgrade -e /app/steinbock[IMC,DeepCell]

USER steinbock
WORKDIR /data
ENTRYPOINT ["python3", "-m", "steinbock"]
