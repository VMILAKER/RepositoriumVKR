


import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_frontend_url
from src import routers

app = FastAPI()
app.include_router(routers.router, prefix='/repositorium')


origins = [get_frontend_url()]
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


if __name__ == '__main__':
    # Base.metadata._all(engine)
    # for i in os.listdir('./app/compressed'):
    #     os.remove(f'./app/compressed/{i}')
    # for j in os.listdir('./app/full_pdf'):
    #     os.remove(f'./app/full_pdf/{j}')
    # asyncio.run(init_models())
    uvicorn.run(app='main:app', host='0.0.0.0',
                port=8000, reload=True, workers=3)
