FROM postgres:{{ cookiecutter.postgresql_version }}

RUN apt-get update \
    && apt-get install -y postgresql-{{ cookiecutter.postgresql_version }}-pgvector \
    && rm -rf /var/lib/apt/lists/*
