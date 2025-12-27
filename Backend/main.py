import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src import FRONTEND_CONFIG

from src import routers
from src.database import Base, engine

app = FastAPI()
app.include_router(routers.router, prefix='/repositorium')


origins = [FRONTEND_CONFIG['url'], 'http://10.6.41.116:5174']
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


if __name__ == '__main__':
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    uvicorn.run(app='main:app', host='0.0.0.0',
                port=8000, reload=True, workers=3)
