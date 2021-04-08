FROM ubuntu:20.04

ARG ILASTIK_BINARY=ilastik-1.3.3post3-Linux.tar.bz2
ARG CELLPROFILER_VERSION=v4.1.3
ARG CELLPROFILER_PLUGINS_VERSION=v4.2.1

RUN apt-get update && apt-get install -y ca-certificates locales wget git build-essential python3-pip
RUN echo "deb mirror://mirrors.ubuntu.com/mirrors.txt focal main restricted universe multiverse " > /etc/apt/sources.list && \
    echo "deb mirror://mirrors.ubuntu.com/mirrors.txt focal-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb mirror://mirrors.ubuntu.com/mirrors.txt focal-security main restricted universe multiverse" >> /etc/apt/sources.list

ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ilastik

RUN wget https://files.ilastik.org/$ILASTIK_BINARY && \
    mkdir /opt/ilastik && \
    tar xjf $ILASTIK_BINARY -C /opt/ilastik --strip-components=1 && \
    rm $ILASTIK_BINARY

# cellprofiler

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    default-libmysqlclient-dev \
    libgtk-3-dev \
    libnotify-dev \
    libsdl2-dev \
    openjdk-11-jdk-headless
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

RUN wget https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    pip3 install numpy wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    rm wxPython-4.1.0-cp38-cp38-linux_x86_64.whl

RUN git clone -b $CELLPROFILER_VERSION --depth 1 https://github.com/CellProfiler/CellProfiler.git && \
    pip3 install ./CellProfiler && \
    rm -r CellProfiler
ENV PATH=$PATH:/home/ubuntu/.local/bin

# cellprofiler plugins

RUN git clone -b $CELLPROFILER_PLUGINS_VERSION https://github.com/BodenmillerGroup/ImcPluginsCP.git && \
    cp -r ImcPluginsCP/plugins /opt/cellprofiler_plugins && \
    rm -r ImcPluginsCP

# steinbock

COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

COPY . /app
ENV PYTHONPATH=$PYTHONPATH:/app

RUN mkdir /data
WORKDIR /data
ENTRYPOINT ["python3", "-m", "steinbock"]
