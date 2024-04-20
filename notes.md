## Docker commands for local development

```bash
mkdir -p ${HOME}/minio/data

docker run \
    -d \
    -p 9000:9000 \
    -p 9001:9001 \
    --user $(id -u):$(id -g) \
    --name minio1 \
    -e "MINIO_ROOT_USER=ROOTUSER" \
    -e "MINIO_ROOT_PASSWORD=PASSWORD" \
    -v ${HOME}/minio/data:/data \
    quay.io/minio/minio server /data --console-address ":9001"


docker pull marqoai/marqo:latest
docker rm -f marqo
docker run --name marqo -dit -p 8882:8882 marqoai/marqo:latest

brew install postgresql
brew services start postgresql
psql postgres

CREATE USER local WITH PASSWORD 'password';
CREATE DATABASE clevercloud;
GRANT ALL PRIVILEGES ON DATABASE clevercloud TO local;
\q
```

You can access Minio at http://localhost:9000 and Marqo at http://localhost:8882.

Go to http://localhost:9001 to access Minio's web console.

Login with ROOTUSER and PASSWORD, create a bucket called `clevercloud`.

Create an Access Key, copy the Access Key and Secret Key for the .env.


Set .env to:
```

```

