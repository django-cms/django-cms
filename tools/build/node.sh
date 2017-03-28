#!/bin/bash

set -e

source $NVM_DIR/nvm.sh
nvm install $NODE_VERSION
nvm alias default $NODE_VERSION
nvm use default

npm install -g npm@"$NPM_VERSION"
npm install -g gulp bower
