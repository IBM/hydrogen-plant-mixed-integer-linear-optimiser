# Data Dictionary for Hydrogen Production Simulations

The `lpmodel.py` script can perform simulations to provide insight to Alex, the plant manager of a Hydrogen Production plant.

Given the input data, the outputs simulate the future state of the Hydrogen Production plant to support Alex to make operational decisions.
- The `optimal` simulation is optimising for cost: showing how Alex could purchase energy at as low a cost as possible whilst still meeting his other operational constraints. This uses a Multi-Integer Programming (MIP) Model. Given forecast hydrogen demand, energy availabilty and energy prices, the model outputs the recommended mix of energy to purchase, and rate at which to run the electrolysers. 
- The `hypotheticalWindOnly` simulation shows what is expected happen if no grid electricity is purchased during the timeframe of the simulation. This simulation does not use a MIP model, it simply assumes all available electricity will be purchased from the local wind farm, as long as the plant has the capacity to consume it.
- Further simulations could be added in future to allow Alex to explore and compare other scenarios

This document defines the input and output variables of the Linear Programming model. Data types listed are Python data types.

## Definition/Explanation of Units
- MW is an instantaneous measure of power 
- Electricity is charged in MWh - if you run a 1 MW motor for an hour, it will consume 1 MWh of electricity
- rates of change can be expressed in MWh per hour, but this cancels done to MW
- We measure electricity in MW and MWh, but hydrogen volume in m^3

## Input Data

### Config
|Name|Definition|Data Type|Possible Values|Units|Comments|
|---|---|---|---|---|---|
|**range:**|   |   |   |   |   |
|periods|number of time periods we choose to do the optimisation for. Each period is of length `periodDuration`|int|> 0|n/a|Model will ingest the number of inputs it is given - determined by the input file|
|periodDuration|duration of each time period in `periods`, Chosen time period over which we do the optimisation - hence input data and output data are grouped by periods|float|   |hours|Currently working with 0.5 hour periods (so 48 periods in a day)|
||   |   |   |   |   |
|**productionLimits:**|   |   |   |   |   |
|maxProductionPh|maximum amount of hydrogen the electrolysers can produce per hour i.e. running at maximum capacity, and therefore using maximum power|float|   |m^3 per hour|This is currently modeled for the plant as a whole, not per individual electrolysers.|
|productionFactor|how much hydrogen is produced from the amount of electrical energy used|float|   |m^3 per MWh|this factor is an attribute of the electrolyser|
|maxPowerChangePh|maximum permissible change to power consumption per hour|float|   |MWh|Used to limit the ramp up and ramp down of hydrogen production, so machinery is not constantly switched on and off.|
|minProductionRate|minimum fraction of `maxProductionPh` at which the electrolyser can run (below this, it would need to be switched off).|float|Must be between 0 and 1.|n/a||
||   |   |   |   |   |
|**storage:**|   |   |   |   |   |
|initialStorage|amount of hydrogen stored at the beginning of the first period you are forecasting|int|Less than or equal to `maxStorage`, greater than or equal to `minStorageSetPoint`|m^3|Technically could be less than `minStorageSetPoint` since this `minStorageSetPoint` is a business rule not a physical constraint, but `initialStorage` can not be below 0.|
|maxStorage|maximum hydrogen storage capacity of the storage tanks|int|Greater than 0|m^3|   |
|minStorageSetPoint|minimum permissible level of hydrogen in the storage tanks (as per business rules) |int|Greater than or equal to 0|m^3|   |




### Forecasts
|Name|Definition|Data Type|Possible Values|Units|Comments?|
|---|---|---|---|---|---|
|timestamp|describes the start time of the time period a given "forecast" input object is refering to|string (datetime)|Currently in format "ignored-0", "ignored-1" etc.|n/a|   |
|renewableGeneration|forecast rate at which renewable energy will be generated during this period|float|Greater than or equal to 0|MW|   |
|hydrogenDemand|forecast volume of hydrogen to be used by customers/consumers during this period|float|Greater than or equal to 0|m^3|   |
|gridPrice|price to purchase energy from the Grid during this time period|float|Can be negative or positive|£/MWh|Note, grid price can be negative when there is high production and low demand.|
|renewablePrice|price to purchase energy from a local renewable source during this time period. This does NOT include power generated for the Grid from renewable sources.|float|Can be negative or positive|£/MWh||

## Output Data
The overall json output contains:
|Name|TimeDB Name|Definition|Data Type|Possible Values|Units|Comments|
|---|---|---|---|---|---|---|
|simulations|n/a|contains simulation results, listed by timestep|list|n/a|n/a|See [Simulations](#simulations)  |
|statusOfOptimalModel|n/a|status of the model returned from the Linear Programming solver|string|Optimal, Not Solved, Infeasible, Unbounded, Undefined|n/a|Desired value is "Optimal", other statuses indicate solver has not found an optimal solution for the simulation, and may not have returned any data|
|units|n/a|object specifying the units for values returned within the `simulations` object|object|items within this object have values that are of type `str` or `null`|n/a|   |
### Simulations
`simulations` is a list of objects. Each object contains:
|Name|TimeDB Name|Definition|Data Type|Possible Values|Units|Comments|
|---|---|---|---|---|---|---|
|timestamp|timestamp|describes the start time of the time period the object is referring to|string|    |n/a|   |
|optimal|n/a|based on the outputs of the linear programming solver: suggested/forecast values for this time period|object|    |n/a|   |
|hypotheticalWindOnly|n/a|based on a simulation where only wind power is purchased: forecast values for this time period|object|    |n/a|NB: this does not use output from the linear programming solver|

The objects for the different simulation types (`optimal` and `hypotheticalWindOnly`) both have the same structure. Names in bold are objects that contain the items listed directly below them:

> **Note**: TimeDB names are given for the optimal simulation valyes. For the `hypotheticalWindOnly` simulation, replace "optimal" with "windonly" e.g. `optimal_electricityusage_wind` becomes `windonly_electricityusage_wind` 

|Name|TimeDB Name|Definition|Data Type|Possible Values|Units|Comments|
|---|---|---|---|---|---|---|
|**electricityUsage**|n/a|quantity of electrical energy that will purchased, and consumed by the electrolyser during this time period|object|    |n/a||
|wind|optimal_electricityusage_wind|`electricityUsage` of electrical energy purchased directly from renewable sources|float|Greater than or equal to 0|MWh|This does NOT include power generated for the Grid from renewable sources.|
|grid|optimal_electricityusage_grid|`electricityUsage` of electrical energy purchased from the grid|float|Greater than or equal to 0|MWh|   |
|total|optimal_electricityusage_total|total `electricityUsage` for this time period: sum of `wind` and `grid`|float|Greater than or equal to 0|MWh|   |
||||||||
|**electricityCost**|n/a|cost of electrical energy purchased during this period|object|    |n/a|Values can be negative, when `gridPrice` or `renewablePrice` are negative|
|wind|optimal_electricitycost_wind|`electricityCost` of electrical energy purchased directly from renewable sources|float|Can be negative or positive|£|This does NOT include power generated for the Grid from renewable sources.|
|grid|optimal_electricitycost_grid|`electricityCost` of electrical energy purchased from the grid|float|Can be negative or positive|£||
|total|optimal_electricitycost_total|total `electricityCost` for this time period: sum of `wind` and `grid`|float|Can be negative or positive|£|   |
||||||||
|**electricityCostCumulative**|n/a|cumulative cost of electrical energy purchased during this time period, and all previous time periods in the simulation|object|    |n/a|Negative values possible, but unusual since we expect elec prices to mostly be positive|
|wind|optimal_electricitycostcumulative_wind|`electricityCostCumulative` of electrical energy purchased directly from renewable sources|float| Can be negative or positive|£|   |
|grid|optimal_electricitycostcumulative_grid|`electricityCostCumulative` of electrical energy purchased from the grid|float|Can be negative or positive|£|   |electricityCostCumulative
|total|optimal_electricitycostcumulative_total|total `electricityCostCumulative`: sum of `wind` and `grid`|float|Can be negative or positive|£|   |
||||||||
|**hydrogenProduced**|n/a|volume of hydrogen that will be produced during this time period|object|    |n/a|   |
|wind|optimal_hydrogenproduced_wind|`hydrogenProduced` using only electrical energy purchased directly from renewable sources|float|Greater than or equal to 0|m^3|   |
|grid|optimal_hydrogenproduced_grid|`hydrogenProduced` using electrical energy purchased from the grid|float|Greater than or equal to 0|m^3|   |
|total|optimal_hydrogenproduced_total|total `hydrogenProduced`: sum of `wind` and `grid`|float|Greater than or equal to 0|m^3|   |
||||||||
|hydrogenInStorage|optimal_hydrogeninstorage|volume of hydrogen that will be in storage at the end of this time period|float|Greater than or equal to 0|m^3|   |
||||||||
|electrolyserOn|optimal_electrolyseron|Operational status of the electrolyser: 1 = on, 0 = off|bool|0 or 1|n/a|   |


## Columns in TimeDB not related to model
- `consumed`: used to track which datasources have consumed a given row of data 
## Assumptions, Limitations and Areas for Exploration 
Considerations for Beta
- e.g. the efficiency of the electrolyser may change based on equipment (and also may change over time) - varying calorific value
- splitting out equipment separately (model each elextrolyser separately)
- model other equipment e.g. compression also consumes energy
- water consumption - and energy used to power pumps
- water storage? you may be able to pump water now, but not need to generate the hydrogen yet e.g. if you are at hydrogen storage capacity
- Modelling maintenance schedule for storage/electrolysers etc
- GET MORE FROM ERWIN
