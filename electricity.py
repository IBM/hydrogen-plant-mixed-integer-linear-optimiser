from pydantic import BaseModel, conlist


# --------------------------------------------------------
#  INPUTS
# --------------------------------------------------------

class ForecastItem(BaseModel):
    # unique identifier for the 30-minute window
    timestamp: str
    # forecast for renewable generation in MWh for a 30-minute window
    renewableGeneration: float
    # forecast for hydrogen demand in m^3 for a 30-minute window
    hydrogenDemand: float
    # forecast for the price of electricity from the grid in £/MWh
    gridPrice: float
    # forecast for the price of renewable energy in £/MWh
    renewablePrice: float

class ProductionLimitsConfiguration(BaseModel):
    # in m^3 per hour
    maxProductionPh: int
    # in m^3 per MWh
    productionFactor: int
    # in MWh
    maxPowerChangePh: float
    # proportion of electrolyser maximum
    #   (e.g. 0.15 would mean 15% of electrolyser maximum)
    minProductionRate: float

class StorageConfiguration(BaseModel):
    # in m^3
    initialStorage: int
    # in m^3
    maxStorage: int
    # in m^3
    minStorageSetPoint: int

class RangeConfiguration(BaseModel):
    # number of periods being considered
    periods: int
    # duration of a period in hours
    periodDuration: float

class ModelConfiguration(BaseModel):
    range: RangeConfiguration
    productionLimits: ProductionLimitsConfiguration
    storage: StorageConfiguration

class Forecast(BaseModel):
    config: ModelConfiguration
    forecasts: conlist(item_type=ForecastItem, min_items=1, unique_items=False)


# --------------------------------------------------------
#  OUTPUTS
# --------------------------------------------------------

class ElectricitySourceType(BaseModel):
    # Sub-items to split output variables by different electricity sources
    wind: float
    grid: float
    total: float

class SimulationOutputPerPeriod(BaseModel):
    electricityUsage: ElectricitySourceType
    electricityCost: ElectricitySourceType
    electricityCostCumulative: ElectricitySourceType
    hydrogenProduced: ElectricitySourceType
    hydrogenInStorage: float
    electrolyserOn: bool

class OutputUnits(BaseModel):
    electricityUsage: str
    electricityCost: str
    electricityCostCumulative: str
    hydrogenProduced: str
    hydrogenInStorage: str
    electrolyserOn: None

class SimulationType(BaseModel):
    timestamp: str
    optimal: SimulationOutputPerPeriod
    hypotheticalWindOnly: SimulationOutputPerPeriod

class SimulationOutput(BaseModel):
    simulations: conlist(item_type=SimulationType, min_items=1, unique_items=False)
    statusOfOptimalModel: str
    units: OutputUnits
