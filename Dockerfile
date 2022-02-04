ARG TENSORFLOW_VERSION=2.5.1
ARG TENSORFLOW_SUFFIX=

FROM tensorflow/tensorflow:${TENSORFLOW_VERSION}${TENSORFLOW_SUFFIX}

ARG STEINBOCK_VERSION
ARG TENSORFLOW_VERSION
ARG TENSORFLOW_SUFFIX
ARG FIXUID_VERSION=0.5.1
ARG ILASTIK_BINARY=ilastik-1.3.3post3-Linux.tar.bz2
ARG CELLPROFILER_VERSION=4.2.1
ARG CELLPROFILER_PLUGINS_VERSION=4.2.1
ARG TZ=Europe/Zurich

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE="1" PYTHONUNBUFFERED="1"

RUN apt-get update && apt-get install -y build-essential git locales python3.8 python3.8-dev python3.8-venv

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"

RUN ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && echo "${TZ}" > /etc/timezone

RUN addgroup --gid 1000 steinbock && \
    adduser --uid 1000 --ingroup steinbock --disabled-password --gecos "" steinbock

RUN python3.8 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --upgrade tensorflow${TENSORFLOW_SUFFIX}==${TENSORFLOW_VERSION}

RUN mkdir /data && \
    chown steinbock:steinbock /data

# fixuid

RUN USER=steinbock && \
    GROUP=steinbock && \
    curl -SsL "https://github.com/boxboat/fixuid/releases/download/v${FIXUID_VERSION}/fixuid-${FIXUID_VERSION}-linux-amd64.tar.gz" | tar -C /usr/local/bin -xzf - && \
    chmod 4755 /usr/local/bin/fixuid && \
    mkdir -p /etc/fixuid
COPY fixuid.yml /etc/fixuid/config.yml

# ilastik

RUN mkdir /opt/ilastik && \
    curl -SsL "https://files.ilastik.org/${ILASTIK_BINARY}" | tar -C /opt/ilastik -xjf - --strip-components=1

# cellprofiler

RUN apt-get install -y libmysqlclient-dev libnotify-dev libsdl2-dev libwebkitgtk-3.0 openjdk-11-jdk-headless
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"

RUN curl -SsO https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04/wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    python -m pip install --upgrade numpy wheel wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    rm wxPython-4.1.0-cp38-cp38-linux_x86_64.whl

RUN python -m pip install --upgrade "cellprofiler==${CELLPROFILER_VERSION}"

# cellprofiler plugins

RUN mkdir /opt/cellprofiler_plugins && \
    curl -SsL "https://github.com/BodenmillerGroup/ImcPluginsCP/archive/refs/tags/v${CELLPROFILER_PLUGINS_VERSION}.tar.gz" | tar -C /opt/cellprofiler_plugins -xzf - "ImcPluginsCP-${CELLPROFILER_PLUGINS_VERSION}/plugins/" --strip-components=2

# steinbock

COPY requirements.txt /app/steinbock/requirements.txt
COPY requirements_deepcell${TENSORFLOW_SUFFIX}.txt /app/steinbock/requirements_deepcell${TENSORFLOW_SUFFIX}.txt
RUN python -m pip install --upgrade -r /app/steinbock/requirements_deepcell${TENSORFLOW_SUFFIX}.txt && \
    python -m pip install --no-deps deepcell==0.11.0 && \
    python -m pip install --upgrade -r /app/steinbock/requirements.txt
ENV TF_CPP_MIN_LOG_LEVEL="2" NO_AT_BRIDGE="1"

RUN mkdir -p /opt/keras/models && \
    curl -SsL https://deepcell-data.s3-us-west-1.amazonaws.com/saved-models/MultiplexSegmentation-7.tar.gz | tar -C /opt/keras/models -xzf - && \
    rm /opt/keras/models/._MultiplexSegmentation

COPY conftest.py MANIFEST.in pyproject.toml setup.cfg setup.py /app/steinbock/
COPY steinbock /app/steinbock/steinbock/
RUN --mount=source=.git,target=/app/steinbock/.git SETUPTOOLS_SCM_PRETEND_VERSION="${STEINBOCK_VERSION#v}" pip install -e "/app/steinbock[all]"

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /data
USER steinbock:steinbock
ENTRYPOINT ["/app/entrypoint.sh"]
