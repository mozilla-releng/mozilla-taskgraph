FROM alpine:3.19.1
LABEL maintainer="Mozilla Release Engineering <release+docker@mozilla.com>"

# Add worker user
RUN mkdir /builds && \
    adduser -h /builds/worker -s /bin/ash -D worker && \
    mkdir /builds/worker/artifacts && \
    chown worker:worker /builds/worker/artifacts

# Update repositories
RUN apk update

# Setup Python
RUN apk add --no-cache python3 py3-pip && \
    ln -sf python3 /usr/bin/python

# Setup other dependencies
RUN apk add bash coreutils git

# %include-run-task

ENV SHELL=/bin/ash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache

# Set a default command useful for debugging
CMD ["/bin/ash"]
