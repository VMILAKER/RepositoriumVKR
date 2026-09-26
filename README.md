# Structure
In this version of RepositoriumVKR asynchronous MinIO and Ollama were connected in order to make project compact and robust, PostgeSQL got asynchronous version as well. 

![Routing scheme of advanced version RepositoriumVKR](https://github.com/VMILAKER/RepositoriumVKR/blob/advanced_version/Images/Repositorium_advanced.jpg)
*Figure 1. Data transmission logic of advanced version RepositoriumVKR*

Project tree (only Backend and Frontend folders attached)
```
├── Backend
│  ├── .dockerignore
│  ├── .env.example
│  ├── .gitignore
│  ├── alembic
│  │  ├── env.py
│  │  ├── README
│  │  ├── script.py.mako
│  │  └── versions/
│  ├── alembic.ini
│  ├── config.py
│  ├── docker-compose.yaml
│  ├── Dockerfile
│  ├── fonts
│  │  └── TNR.ttf
│  ├── main.py
│  ├── requirements.txt
│  ├── src
│  │  ├── database.py
│  │  ├── dto.py
│  │  ├── models.py
│  │  ├── routers.py
│  │  └── services.py
│  └── utilities.py
├── Frontend
│  ├── .env.example
│  ├── .gitignore
│  ├── docker-compose.yaml
│  ├── Dockerfile
│  ├── eslint.config.js
│  ├── index.html
│  ├── package-lock.json
│  ├── package.json
│  ├── README.md
│  ├── src
│  │  ├── App.css
│  │  ├── App.jsx
│  │  ├── components
│  │  │  ├── PdfViewer.jsx
│  │  │  ├── SearchPage.jsx
│  │  │  ├── UploadPage.jsx
│  │  │  └── Utilities.jsx
│  │  ├── index.css
│  │  └── main.jsx
│  └── vite.config.js
```
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

