
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8.2-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN apt-get update -y \
    && apt-get install -y build-essential curl

ENV NODE_VERSION 10.15.1
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash
RUN . $HOME/.nvm/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default \
    && npm install

RUN pip3 install --no-cache-dir -r requirements.txt

#RUN echo 'source $NVM_DIR/nvm.sh' >> $BASH_ENV
#RUN echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> $BASH_ENV
#RUN echo 'source activate public-tree-map' >> $BASH_ENV

RUN ["/bin/bash", "-c", ". $HOME/.nvm/nvm.sh && make release-gc"]