FROM ghcr.io/astral-sh/uv:0.11.1 AS uv
FROM python:3.14.3-slim

WORKDIR /usr/src/app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY ddw ./ddw
ENV PYTHONPATH=.
CMD [ "uv", "run", "--no-sync", "python", "ddw/app.py" ]
