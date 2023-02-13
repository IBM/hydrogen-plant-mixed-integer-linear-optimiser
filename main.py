from fastapi import FastAPI

from app.electricity import Forecast, SimulationOutput
from app.lpmodel import runSimulations


app = FastAPI()


@app.get("/")
def read_root():
    return {"ok": "true"}

@app.post("/electricity/hydrogen-production-optimisation", response_model=SimulationOutput)
def applyLpModel(input: Forecast):
    return runSimulations(input)
