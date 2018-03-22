FROM dbsmith88/py-gdal

# Overwrite the uWSGI config
COPY uwsgi.ini /etc/uwsgi/

COPY . /src/
WORKDIR /src/

EXPOSE 7888
CMD ["uwsgi", "/etc/uwsgi/uwsgi.ini"]
