from fastapi import FastAPI
from api.routers import schedule_router

app = FastAPI(
    title="JobShop Scheduler API",
    description="API para resolver Job Shop Scheduling Problems",
    version="1.0.0",
)

# Montar el router
app.include_router(schedule_router.router, prefix="/schedule", tags=["Schedule"])


@app.get("/")
def root():
    return {"message": "JobShop Scheduler API is running!"}
