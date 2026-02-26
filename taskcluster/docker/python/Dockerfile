# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM debian:13-slim@sha256:f6e2cfac5cf956ea044b4bd75e6397b4372ad88fe00908045e9a0d21712ae3ba
LABEL maintainer="Mozilla Release Engineering <release+mozilla-taskgraph@mozilla.com>"

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.task-cache/uv

# Add worker user
RUN mkdir -p /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker && \
    mkdir /builds/worker/artifacts

# %include-run-task

RUN apt-get update \
 && apt-get install -y --reinstall ca-certificates \
 && apt-get install -y --force-yes --no-install-recommends \
    build-essential \
    zlib1g-dev \
    libssl-dev \
    mercurial \
    git

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

# uv
COPY --from=ghcr.io/astral-sh/uv:0.10.6@sha256:2f2ccd27bbf953ec7a9e3153a4563705e41c852a5e1912b438fc44d88d6cb52c /uv /bin/uv
# %ARG PYTHON_VERSIONS
RUN uv python install $PYTHON_VERSIONS
RUN chown -R worker:worker /builds/worker

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
