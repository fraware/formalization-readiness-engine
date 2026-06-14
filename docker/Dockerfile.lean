FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive ELAN_HOME=/root/.elan PATH="/root/.elan/bin:${PATH}"
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git && rm -rf /var/lib/apt/lists/* \
 && curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y --default-toolchain stable
WORKDIR /workspace
COPY lean lean
RUN cd lean && lake update && lake build
CMD ["bash","-lc","tail -f /dev/null"]
