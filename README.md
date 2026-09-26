# Installation
**!Be aware that your machine supports X86-64-V2!** If does not, you have to implement images for minio, ollama and postgres that satisfy your machine requirements.
## Backend
Get Backend path and copy .env
```
# 1. Get Backend path
cd Backend

# 2. Copy .env.example to .env
cp .env.example .env
```
Next step is build docker compose and picking up container
```
# 3. Build Docker container
docker compose build

# 4. Pick up the container
docker compose up
```
## Frontend
The sequence of actions for Frontend launch is the as same as Backend mounting
```
# 1. Get Frontend path
cd Frontend

# 2. Copy .env.example to .env
cp .env.example .env
```
Next step is build docker compose and picking up container
```
# 3. Build Docker container
docker compose build

# 4. Pick up the container
docker compose up
```

