FROM odoo:{{ cookiecutter.odoo_version }}

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip \
    {% if cookiecutter.odoo_version in ['19.0', '18.0'] %}
    && pip3 install ruff --break-system-packages
    {% else %}
    && pip3 install ruff
    {% endif %}
    && rm -rf /var/lib/apt/lists/*

USER odoo
