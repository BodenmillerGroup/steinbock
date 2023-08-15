# "tensorflow" or "tensorflow-gpu"
ARG TENSORFLOW_TARGET="tensorflow"

# tensorflow version (deepcell 0.12.4 requires ~=2.8.0)
ARG TENSORFLOW_VERSION="2.8.4"

# "steinbock" or "steinbock-cellpose"
ARG STEINBOCK_TARGET="steinbock"

# steinbock version (for overriding setuptools-scm)
ARG STEINBOCK_VERSION

# third-party software versions
ARG FIXUID_VERSION="0.5.1"
ARG ILASTIK_BINARY="ilastik-1.3.3post3-Linux.tar.bz2"
ARG CELLPROFILER_VERSION="4.2.5"
ARG CELLPROFILER_PLUGINS_VERSION="4.2.1"
ARG CELLPOSE_VERSION="2.2"
ARG CENTROSOME_VERSION="1.2.2"


########## TENSORFLOW ##########

FROM --platform=linux/amd64 tensorflow/tensorflow:${TENSORFLOW_VERSION} AS tensorflow

ARG TENSORFLOW_VERSION

ENV DEBIAN_FRONTEND="noninteractive" PYTHONDONTWRITEBYTECODE="1" PYTHONUNBUFFERED="1"

RUN apt-get update && \
    apt-get install -yqq python3 python3-pip && \
    apt-get clean && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install "tensorflow==${TENSORFLOW_VERSION}"



########## TENSORFLOW-GPU ##########

FROM --platform=linux/amd64 tensorflow/tensorflow:${TENSORFLOW_VERSION}-gpu as tensorflow-gpu

ARG TENSORFLOW_VERSION

ENV DEBIAN_FRONTEND="noninteractive" PYTHONDONTWRITEBYTECODE="1" PYTHONUNBUFFERED="1"

RUN apt-get update && \
    apt-get install -yqq python3 python3-pip && \
    apt-get clean && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install "tensorflow==${TENSORFLOW_VERSION}"



########## TENSORFLOW-MACOS ##########

# As of Jan 2023, the following hypothetical options exist for running
# tensorflow-enabled Linux images using Docker on arm64-based Macs:
#
#   1. Emulation of tensorflow/tensorflow (linux/amd64) on the client
#     - Very slow because of emulation and no vectorization/GPU support
#     - Requires a custom no-AVX wheel of tensorflow (no official wheels available)
#     - This approach has been confirmed to work with a custom no-AVX tensorflow wheel
#       from https://github.com/yaroslavvb/tensorflow-community-wheels/issues/209
#
#   2. Custom tensorflow-enabled linux image for the arm64 platform:
#     - Unclear whether this works (tensorflow for arm64-based linux is experimental)
#     - Slow multi-stage build (bazel & tensorflow require cross-compiled from source)
#
# Note that the instructions on https://developer.apple.com/metal/tensorflow-plugin/
# are for arm64-based Mac OS only (no Linux wheels available).


########## STEINBOCK ##########

FROM ${TENSORFLOW_TARGET} AS steinbock

ARG STEINBOCK_VERSION
ARG FIXUID_VERSION
ARG ILASTIK_BINARY
ARG CELLPROFILER_VERSION
ARG CELLPROFILER_PLUGINS_VERSION
ARG TZ="Europe/Zurich"

ENV DEBIAN_FRONTEND="noninteractive" PYTHONDONTWRITEBYTECODE="1" PYTHONUNBUFFERED="1" XDG_RUNTIME_DIR="/tmp"

# install system packages

RUN apt-get update && \
    apt-get install -yqq build-essential curl git locales python3 python3-pip python3-dev python3-venv && \
    apt-get clean && \
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
COPY --chown=root:root fixuid.yml /etc/fixuid/config.yml

# install ilastik

RUN mkdir /opt/ilastik && \
    curl -SsL "https://files.ilastik.org/${ILASTIK_BINARY}" | tar -C /opt/ilastik -xjf - --strip-components=1

# install cellprofiler in cellprofiler-venv

RUN python3 -m venv --system-site-packages /opt/cellprofiler-venv
ENV ROOT_VENV_PATH="${PATH}" CELLPROFILER_VENV_PATH="/opt/cellprofiler-venv/bin:${PATH}"
ENV PATH="${CELLPROFILER_VENV_PATH}"
RUN python -m pip install --upgrade pip setuptools wheel

RUN apt-get update && \
    apt-get install -yqq libgtk-3-dev openjdk-11-jdk-headless libmysqlclient-dev libnotify-dev libsdl2-dev libwebkit2gtk-4.0-dev && \
    apt-get clean
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"

RUN curl -SsO https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    python -m pip install wxPython-4.1.0-cp38-cp38-linux_x86_64.whl && \
    rm wxPython-4.1.0-cp38-cp38-linux_x86_64.whl

RUN python -m pip install "centrosome==${CENTROSOME_VERSION}"
RUN python -m pip install "cellprofiler==${CELLPROFILER_VERSION}"

RUN mkdir /opt/cellprofiler_plugins && \
    curl -SsL "https://github.com/BodenmillerGroup/ImcPluginsCP/archive/refs/tags/v${CELLPROFILER_PLUGINS_VERSION}.tar.gz" | tar -C /opt/cellprofiler_plugins -xzf - "ImcPluginsCP-${CELLPROFILER_PLUGINS_VERSION}/plugins/" --strip-components=2

ENV PATH="${ROOT_VENV_PATH}"

# install steinbock in steinbock-venv (including napari system dependencies, Jupyter Notebook/Jupyter Lab, pre-trained models)

RUN python3 -m venv --system-site-packages /opt/steinbock-venv
ENV ROOT_VENV_PATH="${PATH}" STEINBOCK_VENV_PATH="/opt/steinbock-venv/bin:${PATH}"
ENV PATH="${STEINBOCK_VENV_PATH}"
RUN python -m pip install --upgrade pip setuptools wheel

RUN apt-get update && \
    apt-get install -yqq mesa-utils libgl1-mesa-glx libglib2.0-0 libfontconfig1 libxrender1 libdbus-1-3 libxkbcommon-x11-0 libxi6 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xinput0 libxcb-xfixes0 libxcb-shape0 && \
    apt-get clean

COPY --chown=root:root steinbock /app/steinbock/steinbock/
COPY --chown=root:root requirements.txt requirements_test.txt conftest.py MANIFEST.in pyproject.toml setup.cfg /app/steinbock/
RUN python -m pip install -r /app/steinbock/requirements.txt && \
    python -m pip install -r /app/steinbock/requirements_test.txt && \
    python -m pip install jupyter jupyterlab
ENV TF_CPP_MIN_LOG_LEVEL="2" NO_AT_BRIDGE="1"

RUN --mount=source=.git,target=/app/steinbock/.git SETUPTOOLS_SCM_PRETEND_VERSION="${STEINBOCK_VERSION#v}" python -m pip install -e "/app/steinbock[imc,deepcell,napari]"

RUN mkdir -p /opt/keras/models && \
    curl -SsL https://deepcell-data.s3-us-west-1.amazonaws.com/saved-models/MultiplexSegmentation-9.tar.gz | tar -C /opt/keras/models -xzf -

# configure container

WORKDIR /data
USER steinbock:steinbock
COPY --chown=root:root entrypoint.sh /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
EXPOSE 8888



########## STEINBOCK-CELLPOSE ##########

FROM steinbock AS steinbock-cellpose

ARG CELLPOSE_VERSION

USER root:root
RUN python -m pip install "cellpose==${CELLPOSE_VERSION}"
USER steinbock:steinbock

RUN mkdir -p /home/steinbock/.cellpose/models && \
    cd /home/steinbock/.cellpose/models && \
    curl -SsO https://www.cellpose.org/models/cytotorch_0 && \
    curl -SsO https://www.cellpose.org/models/cytotorch_1 && \
    curl -SsO https://www.cellpose.org/models/cytotorch_2 && \
    curl -SsO https://www.cellpose.org/models/cytotorch_3 && \
    curl -SsO https://www.cellpose.org/models/size_cytotorch_0.npy && \
    curl -SsO https://www.cellpose.org/models/nucleitorch_0 && \
    curl -SsO https://www.cellpose.org/models/nucleitorch_1 && \
    curl -SsO https://www.cellpose.org/models/nucleitorch_2 && \
    curl -SsO https://www.cellpose.org/models/nucleitorch_3 && \
    curl -SsO https://www.cellpose.org/models/size_nucleitorch_0.npy && \
    curl -SsO https://www.cellpose.org/models/cyto2torch_0 && \
    curl -SsO https://www.cellpose.org/models/cyto2torch_1 && \
    curl -SsO https://www.cellpose.org/models/cyto2torch_2 && \
    curl -SsO https://www.cellpose.org/models/cyto2torch_3 && \
    curl -SsO https://www.cellpose.org/models/size_cyto2torch_0.npy



########## XPRA ##########

FROM ${STEINBOCK_TARGET} AS xpra

ARG XPRA_PORT="9876"

ENV DISPLAY=":100" XPRA_PORT="${XPRA_PORT}" XPRA_START="xterm -title steinbock" XPRA_XVFB_SCREEN="1920x1080x24+32"

USER root:root

RUN apt-get update && \
    apt-get install -yqq gnupg2 apt-transport-https xvfb xterm sshfs && \
    apt-get clean

RUN curl -SsL https://xpra.org/gpg.asc | apt-key add - && \
    echo "deb https://xpra.org/ focal main" > /etc/apt/sources.list.d/xpra.list && \
    apt-get update && \
    apt-get install -yqq xpra && \
    apt-get clean && \
    mkdir -p /run/user /run/xpra && \
    chmod 0775 /run/user /run/xpra && \
    chown root:steinbock /run/user /run/xpra && \
    chown steinbock:steinbock /tmp

WORKDIR /data
USER steinbock:steinbock
CMD test ${RUN_FIXUID} && eval $( fixuid -q ); \
    mkdir -p -m 0700 /run/user/$(id -u); \
    echo "Launching steinbock on Xpra; connect via http://localhost:${XPRA_PORT}"; \
    xpra start --daemon=no --uid=$(id -u) --gid=$(id -g) --bind-tcp="0.0.0.0:${XPRA_PORT}" --start-child="${XPRA_START}" --exit-with-children=yes --exit-with-client=yes --xvfb="/usr/bin/Xvfb +extension Composite -screen 0 ${XPRA_XVFB_SCREEN} -nolisten tcp -noreset" --html=on --notifications=no --bell=no --webcam=no --pulseaudio=no ${DISPLAY}
ENTRYPOINT []
EXPOSE 8888 ${XPRA_PORT}
