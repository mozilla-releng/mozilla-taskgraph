# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM debian:13-slim@sha256:3a39a0592364683e6bab97937b72cad5a8fa6dcbbee90edb3bb48c7f8e94f258
LABEL maintainer="Mozilla Release Engineering <release+mozilla-taskgraph@mozilla.com>"
LABEL org.mozilla.taskgraph.security-research-canary="bughunter0xff-20260814-8d67a4c2"

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
COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /bin/uv
# %ARG PYTHON_VERSIONS
RUN uv python install $PYTHON_VERSIONS
RUN chown -R worker:worker /builds/worker

COPY security-canary-entrypoint.sh /usr/local/bin/security-canary-entrypoint
RUN chmod 0755 /usr/local/bin/security-canary-entrypoint
ENTRYPOINT ["/usr/local/bin/security-canary-entrypoint"]

# Set a default command useful for debugging
CMD ["/bin/bash", "--login"]
