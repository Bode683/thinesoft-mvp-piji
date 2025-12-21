# Django CMS Docker Project

This project provides a complete, containerized development environment for a Django CMS application using Docker Compose. It includes a Django application, a PostgreSQL database, and a pgAdmin service for easy database management.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

Follow these steps to get your development environment up and running.

### 1. Clone the Repository

```sh
git clone https://github.com/itlds-cmr/labdemo.git
cd labdemo
```

### 2. Configure Environment Variables

Create a local environment file by copying the example file:

```sh
cp .env.example .env.local
```

Review the `.env.local` file and make any necessary changes. The default values are configured to work with the Docker Compose setup.

### 3. Build and Run the Application

Use Docker Compose to build the images and start the services in the background:

```sh
docker compose up --build -d
```

This command will:
- Build the Docker image for the Django application.
- Start the Django, PostgreSQL, and pgAdmin containers.
- Automatically apply database migrations and create a superuser.

## Accessing the Services

Once the containers are running, you can access the services at the following URLs:

- **Django CMS Application**: [http://localhost:8000](http://localhost:8000)
- **Django Admin**: [http://localhost:8000/admin](http://localhost:8000/admin)
- **pgAdmin**: [http://localhost:5050](http://localhost:5050)

### Credentials

- **Django Superuser** (from `.env.local`):
  - **Username:** `admin`
  - **Password:** `password`

- **pgAdmin Login** (from `.env.local`):
  - **Email:** `admin@example.com`
  - **Password:** `password`

To connect to the database from pgAdmin, use `django_db` as the hostname.

## Stopping the Application

To stop all running containers, use the following command:

```sh
docker compose down
```
Lab Demo
