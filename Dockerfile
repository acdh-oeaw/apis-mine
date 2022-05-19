FROM python:3.8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN useradd -ms /bin/bash app_user
WORKDIR /app
COPY . /app/
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
     && apt-get -y install --no-install-recommends gdal-bin graphviz
USER app_user
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "/home/app_user/.local/bin:$PATH"