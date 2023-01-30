# "tensorflow" or "tensorflow-gpu"
ARG TENSORFLOW_TARGET="tensorflow"

# tensorflow version (deepcell 0.12.4 requires ~=2.8.0)
ARG TENSORFLOW_VERSION="2.8.4"

# # ubuntu version (for tensorflow-macos; should match base image of tensorflow/tensorflow:${TENSORFLOW_VERSION})
# ARG UBUNTU_VERSION="20.04"

# # bazelisk version (for tensorflow-macos)
# ARG BAZELISK_VERSION="1.15.0"

########## TENSORFLOW ##########

FROM --platform=linux/amd64 tensorflow/tensorflow:${TENSORFLOW_VERSION} AS tensorflow
ARG TENSORFLOW_VERSION

# install basic tooling
RUN apt-get update && \
    apt-get install -yqq curl python3 python3-pip && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install tensorflow==${TENSORFLOW_VERSION}

########## TENSORFLOW-GPU ##########

FROM --platform=linux/amd64 tensorflow/tensorflow:${TENSORFLOW_VERSION}-gpu as tensorflow-gpu
ARG TENSORFLOW_VERSION

# install basic tooling
RUN apt-get update && \
    apt-get install -yqq curl python3 python3-pip && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install tensorflow==${TENSORFLOW_VERSION}

# ########## TENSORFLOW-MACOS ##########

# FROM --platform=linux/arm64 ubuntu:${UBUNTU_VERSION} as tensorflow-macos
# ARG BAZELISK_VERSION
# ARG TENSORFLOW_VERSION

# # install basic tooling
# RUN apt-get update && \
#     apt-get install -yqq curl python3 python3-pip && \
#     python3 -m pip install --upgrade pip setuptools wheel

# # install bazelisk
# RUN curl -Ss -o /usr/local/bin/bazel "https://github.com/bazelbuild/bazelisk/releases/download/v${BAZELISK_VERSION}/bazelisk-linux-arm64" && \
#     chmod +x /usr/local/bin/bazel && \
#     bazel

# # install tensorflow dependencies
# RUN apt-get update && \
#     apt-get install -yqq python3-dev && \
#     python3 -m pip install --upgrade numpy packaging requests opt_einsum && \
#     python3 -m pip install --upgrade --no-deps keras_preprocessing

# # install tensorflow
# RUN mkdir /opt/tensorflow && \
#     curl -SsL "https://github.com/tensorflow/tensorflow/archive/refs/tags/v${TENSORFLOW_VERSION}.tar.gz" | tar -C /opt/tensorflow -xzf - --strip-components=1 && \
#     cd /opt/tensorflow && \
#     ./configure && \
#     bazel build --local_cpu_resources=1 //tensorflow/tools/pip_package:build_pip_package && \
#     ./bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg && \
#     python3 -m pip install /tmp/tensorflow_pkg/tensorflow-${TENSORFLOW_VERSION}-tags.whl

########## STEINBOCK ##########

FROM ${TENSORFLOW_TARGET} AS steinbock
ARG STEINBOCK_VERSION

# third-party software versions
ARG FIXUID_VERSION="0.5.1"
ARG ILASTIK_BINARY="ilastik-1.3.3post3-Linux.tar.bz2"
ARG CELLPROFILER_VERSION="4.2.5"
ARG CELLPROFILER_PLUGINS_VERSION="4.2.1"

# timezone
ARG TZ="Europe/Zurich"

# environment variables
ENV DEBIAN_FRONTEND="noninteractive" PYTHONDONTWRITEBYTECODE="1" PYTHONUNBUFFERED="1" ORIG_PATH="${PATH}"

# install essential packages
RUN apt-get update && \
    apt-get install -yqq build-essential git locales python3 python3-pip python3-dev python3-venv && \
    python3 -m pip install --upgrade pip setuptools wheel

# set locale and timezone
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"
RUN ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime && echo "${TZ}" > /etc/timezone

# create steinbock user
RUN addgroup --gid 1000 steinbock && \
    adduser --uid 1000 --ingroup steinbock --disabled-password --gecos "" steinbock

# create data directory
RUN mkdir /data && \
    chown steinbock:steinbock /data

# install fixuid
ENV RUN_FIXUID=1
RUN USER=steinbock && \
    GROUP=steinbock && \
    curl -SsL "https://github.com/boxboat/fixuid/releases/download/v${FIXUID_VERSION}/fixuid-${FIXUID_VERSION}-linux-amd64.tar.gz" | tar -C /usr/local/bin -xzf - && \
    chmod 4755 /usr/local/bin/fixuid && \
    mkdir -p /etc/fixuid
COPY fixuid.yml /etc/fixuid/config.yml

# install ilastik
RUN mkdir /opt/ilastik && \
    curl -SsL "https://files.ilastik.org/${ILASTIK_BINARY}" | tar -C /opt/ilastik -xjf - --strip-components=1

# install cellprofiler (install dependencies, including GTK and JVM)
RUN apt-get update && \
    apt-get install -yqq libgtk-3-dev openjdk-11-jdk-headless libmysqlclient-dev libnotify-dev libsdl2-dev libwebkit2gtk-4.0-dev
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"

# install cellprofiler (create virtual environment)
RUN python3 -m venv --system-site-packages /opt/cellprofiler-venv
ENV PATH="/opt/cellprofiler-venv/bin:${ORIG_PATH}"
RUN python -m pip install --upgrade pip setuptools wheel

# install cellprofiler (install wxPython Python dependency)
RUN curl -SsO https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    python -m pip install wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    rm wxPython-4.1.0-cp38-cp38-linux_x86_64.whl

# install cellprofiler (install cellprofiler Python package)
RUN python -m pip install "cellprofiler==${CELLPROFILER_VERSION}"

# install cellprofiler (restore base environment)
ENV PATH="${ORIG_PATH}"

# install cellprofiler (install plugins)
RUN mkdir /opt/cellprofiler_plugins && \
    curl -SsL "https://github.com/BodenmillerGroup/ImcPluginsCP/archive/refs/tags/v${CELLPROFILER_PLUGINS_VERSION}.tar.gz" | tar -C /opt/cellprofiler_plugins -xzf - "ImcPluginsCP-${CELLPROFILER_PLUGINS_VERSION}/plugins/" --strip-components=2

# install steinbock (install dependencies, including napari dependencies)
RUN apt-get update && \
    apt-get install -yqq mesa-utils libgl1-mesa-glx libglib2.0-0 libfontconfig1 libxrender1 libdbus-1-3 libxkbcommon-x11-0 libxi6 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xinput0 libxcb-xfixes0 libxcb-shape0

# install steinbock (create virtual environment)
RUN python3 -m venv --system-site-packages /opt/steinbock-venv
ENV PATH="/opt/steinbock-venv/bin:${ORIG_PATH}"
RUN python -m pip install --upgrade pip setuptools wheel

# install steinbock (install pinned Python requirements)
COPY requirements.txt /app/steinbock/requirements.txt
RUN python -m pip install -r /app/steinbock/requirements.txt
ENV TF_CPP_MIN_LOG_LEVEL="2" NO_AT_BRIDGE="1"

# install steinbock (download pre-trained neural network)
RUN mkdir -p /opt/keras/models && \
    curl -SsL https://deepcell-data.s3-us-west-1.amazonaws.com/saved-models/MultiplexSegmentation-9.tar.gz | tar -C /opt/keras/models -xzf -

# install steinbock (install steinbock Python package)
COPY conftest.py MANIFEST.in pyproject.toml setup.cfg /app/steinbock/
COPY steinbock /app/steinbock/steinbock/
RUN --mount=source=.git,target=/app/steinbock/.git SETUPTOOLS_SCM_PRETEND_VERSION="${STEINBOCK_VERSION#v}" python -m pip install -e "/app/steinbock[imc,cellpose,deepcell,napari,testing]"

# install jupyter (within steinbock-env)
RUN python -m pip install jupyter jupyterlab

# configure container
WORKDIR /data
USER steinbock:steinbock
COPY entrypoint.sh /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
EXPOSE 8888

########## STEINBOCK-XPRA ##########

FROM steinbock as steinbock-xpra

# default exposed Xpra port
ARG XPRA_PORT="9876"

# environment variables
ENV DISPLAY=":100" XPRA_PORT="${XPRA_PORT}" XPRA_START="xterm -title steinbock" XPRA_XVFB_SCREEN="1920x1080x24+32" XDG_RUNTIME_DIR="/tmp"

# restore root and base environment
USER root:root
ENV PATH="${ORIG_PATH}"

# install Xpra (install dependencies)
RUN apt-get update && \
    apt-get install -yqq gnupg2 apt-transport-https xvfb xterm sshfs

# install Xpra (install Xpra package)
RUN curl -SsL https://xpra.org/gpg.asc | apt-key add - && \
    echo "deb https://xpra.org/ focal main" > /etc/apt/sources.list.d/xpra.list && \
    apt-get update && \
    apt-get install -yqq xpra && \
    mkdir -p /run/user /run/xpra && \
    chmod 0775 /run/user /run/xpra && \
    chown root:steinbock /run/user /run/xpra && \
    chown steinbock:steinbock /tmp

# configure container
WORKDIR /data
USER steinbock:steinbock
CMD test ${RUN_FIXUID} && eval $( fixuid -q ); \
    mkdir -p -m 0700 /run/user/$(id -u); \
    echo "Launching steinbock on Xpra; connect via http://localhost:${XPRA_PORT}"; \
    xpra start --daemon=no --uid=$(id -u) --gid=$(id -g) --bind-tcp=0.0.0.0:${XPRA_PORT} --start-child="${XPRA_START}" --exit-with-children=yes --exit-with-client=yes --env=PATH="/opt/steinbock-venv/bin:${ORIG_PATH}" --xvfb="/usr/bin/Xvfb +extension Composite -screen 0 ${XPRA_XVFB_SCREEN} -nolisten tcp -noreset" --html=on --notifications=no --bell=no --webcam=no --pulseaudio=no ${DISPLAY}
ENTRYPOINT []
EXPOSE 8888 ${XPRA_PORT}
