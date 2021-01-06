FROM tensorflow/tensorflow:2.4.0-gpu-jupyter
MAINTAINER Louis Tiao <louistiao@gmail.com>

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections
RUN apt-get update && apt-get install -y --no-install-recommends \
        git-core \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-xetex \
        cm-super \
        dvipng \
        pandoc \
        msttcorefonts \
        poppler-utils \
        imagemagick \
        ffmpeg \
        graphviz \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* ~/.cache/matplotlib

# TODO: copy to temporary dir rather then some unknown current dir
COPY requirements*.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip==20.3.3 keyrings.alt==4.0.2 && \
    python -m pip install --no-cache-dir -r requirements_dev.txt && \
    python -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /usr/src/app

COPY . /usr/src/app
WORKDIR /usr/src/app
RUN python -m pip install --no-deps -e .

CMD ["bash", "-c", "source /etc/bash.bashrc && jupyter notebook --ip 0.0.0.0 --no-browser --allow-root"]
