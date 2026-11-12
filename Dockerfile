FROM ghcr.io/astral-sh/uv:0.11.1 AS uv
FROM python:3.14.10-slim

# Refresh the system CA bundle (eMudhra CA revocation)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY ddw ./ddw
ENV PYTHONPATH=.
CMD [ "uv", "run", "--no-sync", "python", "ddw/app.py" ]
