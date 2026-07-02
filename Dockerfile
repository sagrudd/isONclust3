ARG RUST_IMAGE=rust:1.88-slim-bookworm
ARG RUNTIME_IMAGE=debian:bookworm-slim

FROM ${RUST_IMAGE} AS build
WORKDIR /workspace

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release --locked

FROM ${RUNTIME_IMAGE} AS runtime

LABEL org.opencontainers.image.title="isONclust3" \
      org.opencontainers.image.description="Long-read transcriptome cluster-table producer for newONform" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.source="https://github.com/sagrudd/isONclust3"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /workspace/target/release/isONclust3 /usr/local/bin/isONclust3

WORKDIR /work
ENTRYPOINT ["/usr/bin/tini", "--", "isONclust3"]
CMD ["--help"]
