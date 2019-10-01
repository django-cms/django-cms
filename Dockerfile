# <WARNING>
# Everything within sections like <TAG> is generated and can
# be automatically replaced on deployment. You can disable
# this functionality by simply removing the wrapping tags.
# </WARNING>

# <DOCKER_FROM>
FROM divio/base:4.15-py3.6-slim-stretch
# </DOCKER_FROM>

# <NODE>
ADD tools/build /stack/boilerplate

ENV NODE_VERSION=8.11.0 \
    NPM_VERSION=6.1.0

RUN bash /stack/boilerplate/install.sh

ENV NODE_PATH=$NVM_DIR/versions/node/v$NODE_VERSION/lib/node_modules \
    PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH
# </NODE>

# <PYTHON>
ENV PIP_INDEX_URL=${PIP_INDEX_URL:-https://wheels.aldryn.net/v1/aldryn-extras+pypi/${WHEELS_PLATFORM:-aldryn-baseproject-py3}/+simple/} \
    WHEELSPROXY_URL=${WHEELSPROXY_URL:-https://wheels.aldryn.net/v1/aldryn-extras+pypi/${WHEELS_PLATFORM:-aldryn-baseproject-py3}/}
COPY requirements.* /app/
COPY addons-dev /app/addons-dev/
RUN pip-reqs compile && \
    pip-reqs resolve && \
    pip install \
        --no-index --no-deps \
        --requirement requirements.urls
# </PYTHON>

# <NPM update=no>
# package.json is put into / so that mounting /app for local
# development does not require re-running npm install
ENV PATH=/node_modules/.bin:$PATH

# Only extract if file not empty
COPY package*.json /
RUN (cd / && npm install --production && rm -rf /tmp/*)
# </NPM>

# <SOURCE>
COPY . /app
# </SOURCE>

# <GULP>
ENV GULP_MODE=production
RUN gulp build
# </GULP>

# <STATIC>
RUN DJANGO_MODE=build python manage.py collectstatic --noinput
# </STATIC>