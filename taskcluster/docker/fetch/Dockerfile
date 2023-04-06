FROM debian:11

### Add worker user and setup its workspace.
RUN mkdir /builds && \
    groupadd -g 1000 worker && \
    useradd -u 1000 -g 1000 -d /builds/worker -s /bin/bash -m worker && \
    mkdir -p /builds/worker/workspace && \
    chown -R worker:worker /builds

# Declare default working folder
WORKDIR /builds/worker

RUN apt-get update && \
    apt-get install -y \
      gnupg \
      bzip2 \
      git \
      openssh-client \
      python3-pip \
      python3-requests \
      python3-zstd \
      unzip

# %include-run-task

# %include requirements/base.txt
ADD topsrcdir/requirements/base.txt /builds/worker/base.txt
RUN python3 -mpip install -r base.txt
