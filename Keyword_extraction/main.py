import uvicorn
from fastapi import FastAPI

from routers import router

app = FastAPI()
app.include_router(router, prefix='/gemma_gqw')

if __name__ == '__main__':
    uvicorn.run(app='main:app', host='0.0.0.0',
                port=8001, reload=True, workers=3)
