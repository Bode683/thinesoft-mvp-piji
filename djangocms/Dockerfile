FROM python:3.12-slim-bookworm

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get install -y \
postgresql-client \
build-essential \
gcc \
libxml2-dev \
libxslt1-dev \
zlib1g-dev \
libjpeg62-turbo-dev \
libfreetype6-dev \
libwebp-dev \
libpng-dev \
libtiff5-dev \
&& rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip
# optimizing the docker caching behaviour
# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the application code into the container
COPY . /app/

# collectstatic will be run at runtime in entrypoint for production only

# No CMD here; entrypoint will start Gunicorn or dev server based on DJANGO_ENV

# Set the entrypoint script to be executed when the container starts
ENTRYPOINT ["/app/entrypoint.sh"]