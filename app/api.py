import uvicorn
from database.database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.checkup_route import checkup_route
from routes.home_route import home_route
from routes.ml_task import ml_task_router
from routes.user_route import user_route

app = FastAPI()
app.include_router(home_route)
app.include_router(user_route, prefix="/user")
app.include_router(checkup_route, prefix="/checkup")
app.include_router(ml_task_router, prefix="/ml_task")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
