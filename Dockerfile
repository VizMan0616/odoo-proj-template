FROM ubuntu:jammy
MAINTAINER Odoo S.A. <info@odoo.com>

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Generate locale C.UTF-8 for postgres and general locale data                
ENV LANG C.UTF-8                                                              
ENV TZ=UTC                                                                    
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Retrieve the target architecture to install the correct wkhtmltopdf package
ARG TARGETARCH

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf
RUN apt update \
    && apt install -y --no-install-recommends \
        ca-certificates \
        dirmngr \
        fonts-noto-cjk \
        gnupg \
        gosu \
        gsfonts \
        libssl-dev \
        node-less \
        npm \
        postgresql-client \
        python3-magic \
        python3-num2words \
        python3-pip \
        python3-phonenumbers \
        python3-pyldap \
        python3-qrcode \
        python3-renderpm \
        python3-setuptools \
        python3-slugify \
        python3-vobject \
        python3-watchdog \
        python3-wheel \
        python3-xlrd \
        python3-xlwt \
        xz-utils \
        xfonts-75dpi \
        libx11-6 \
        fontconfig \
        xfonts-base \
        libxrender1 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sLO "https://github.com/wkhtmltopdf/packaging/files/8632951/wkhtmltox_0.12.5-1.jammy_amd64.zip" && \
    unzip wkhtmltox_0.12.5-1.jammy_amd64.zip && \
    dpkg -i "wkhtmltox_0.12.5-1.jammy_amd64.deb"

# # install latest postgresql-client
# RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ bullseye-pgdg main' > /etc/apt/sources.list.d/pgdg.list \
#     && GNUPGHOME="$(mktemp -d)" \
#     && export GNUPGHOME \
#     && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
#     && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
#     && gpg --batch --armor --export "${repokey}" > /etc/apt/trusted.gpg.d/pgdg.gpg.asc \
#     && gpgconf --kill all \
#     && rm -rf "$GNUPGHOME" \
#     && apt-get update  \
#     && apt-get install --no-install-recommends -y postgresql-client \
#     && rm -f /etc/apt/sources.list.d/pgdg.list \
#     && rm -rf /var/lib/apt/lists/*

# Install rtlcss (on Debian buster)
RUN npm install -g rtlcss

# Install Code Quality Tools
RUN pip install isort black pylint_odoo

# Install Odoo
ARG ODOO_VERSION
ARG ODOO_RELEASE
RUN curl -o odoo.deb -sSL http://nightly.odoo.com/${ODOO_VERSION}/nightly/deb/odoo_${ODOO_VERSION}.${ODOO_RELEASE}_all.deb \
    && apt-get update \
    && apt-get -y install --no-install-recommends ./odoo.deb \
    && rm -rf /var/lib/apt/lists/* odoo.deb

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo/

# Set permissions and Mount /var/lib/odoo to allow restoring filestore and /mnt/extra-addons for users addons
RUN chown odoo /etc/odoo/odoo.conf \
    && mkdir -p /mnt/extra-addons \
    && chown -R odoo /mnt/extra-addons \
    && mkdir -p /mnt/custom-addons \
    && chown -R odoo /mnt/custom-addons
VOLUME ["/var/lib/odoo", "/mnt/extra-addons", "/mnt/custom-addons"]

# Expose Odoo services
EXPOSE 8069 8071 8072

# Set the default config file
ENV ODOO_RC /etc/odoo/odoo.conf

COPY [".isort.cfg", ".eslint.yml", ".pylintrc", "/mnt/"]
COPY wait-for-psql.py /usr/local/bin/wait-for-psql.py

# Set default user when running the container
USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
