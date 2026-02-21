import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import FRONTEND_CONFIG, routers
from src.database import Base, engine

app = FastAPI()
app.include_router(routers.router, prefix='/repositorium')


origins = [FRONTEND_CONFIG['url'], 'url']
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


if __name__ == '__main__':
    # Base.metadata.drop_all(engine)
    # for i in os.listdir('./app/compressed'):
    #     os.remove(f'./app/compressed/{i}')
    # for j in os.listdir('./app/full_pdf'):
    #     os.remove(f'./app/full_pdf/{j}')
    Base.metadata.create_all(engine)
    uvicorn.run(app='main:app', host='0.0.0.0',
                port=8000, reload=True, workers=3)
