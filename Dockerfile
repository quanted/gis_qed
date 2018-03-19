FROM python:3

ENV GDAL_VERSION=2.2.1

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

RUN wget http://download.osgeo.org/gdal/$GDAL_VERSION/gdal-${GDAL_VERSION}.tar.gz -O /tmp/gdal-${GDAL_VERSION}.tar.gz && tar -x -f /tmp/gdal-${GDAL_VERSION}.tar.gz -C /tmp

RUN cd /tmp/gdal-${GDAL_VERSION} && \
    ./configure \
        --prefix=/usr \
        --with-python \
        --with-geos \
        --with-sfcgal \
        --with-geotiff \
        --with-jpeg \
        --with-png \
        --with-expat \
        --with-libkml \
        --with-openjpeg \
        --with-pg \
        --with-curl \
        --with-spatialite && \
    make -j $(nproc) && make install

RUN rm /tmp/gdal-${GDAL_VERSION} -rf

# Overwrite the uWSGI config
COPY uwsgi.ini /etc/uwsgi/

COPY . /src/
WORKDIR /src/

EXPOSE 7888
CMD ["uwsgi", "/etc/uwsgi/uwsgi.ini"]
