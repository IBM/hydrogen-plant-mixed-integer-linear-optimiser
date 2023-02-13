from pulp import LpProblem, LpVariable, lpSum
import pulp

#
# input:
#   data about a timeseries - for each time interval:
#    - info about wind / renewable energy
#        - forecast of how much renewable/wind energy will be generated in that time interval
#        - how much that renewable energy will cost
#    - info about national grid
#        - how much grid energy will cost
#    - how much hydrogen demand there will be
#
# create a model
#
#   define inputs:
#      - grid power consumption for a time interval
#      - renewable power consumption for a time interval
#   define output:
#      - whether the electrolyser is on or off
#
# initialise the model with objective function:
#    total cost of energy used (cost of grid energy plus renewable/wind energy used)
#
# initialise the model with constraints:
#
#    1 - can't use more renewable energy than there is available - DONE
#
#    2 - can't produce more hydrogen than the max capability of the hydrolisers - DONE
#
#   3  - hydrogen storage needs to remain above minimum threshold
#
#    4 - hydrogen storage needs to remain under max storage capacity
#
#    - avoid changing power more rapidly than max limit
#    - if the hydroliser is on, it has to produce at least the minimum production amount
#    - if the hydroliser is off, it should produce zero
#
#    - if the hydroliser is off, it should consume no grid or renewable energy
#    - if the hydroliser is on, it ???  should consume some energy - enough to run at least at 15% capacity
#
# run the model
#
# output:
#    for each time interval, the model gives:
#    - how much grid energy to use
#    - how much renewable energy to use
#    - whether the electrolyser should be on or off
#
#    which we add to with additional data, for each time interval:
#    - how much hydrogen will be in storage at this point
#    - how much energy was consumed
#         - from the grid
#         - from renewable / wind
#    - how much the consumed energy cost
#         - from the grid
#         - from renewable / wind
#    - how much hydrogen was produced
#         - using grid energy
#         - using renewable / wind
#
#  we also add a hypothetical, if only renewable energy was used:
#    - how much hydrogen will be in storage at this point
#    - how much energy was consumed
#         - from renewable / wind
#    - how much the consumed energy cost
#         - from renewable / wind
#    - how much hydrogen was produced
#         - using renewable / wind
#

def calculate_elec_needed_to_maintain_min_storage(storage_at_simulation_start, cumulativeHydrogenDemand, minimum_allowed_storage, productionFactor):
    storage_if_no_hydrogen_produced = storage_at_simulation_start - cumulativeHydrogenDemand
    production_to_maintain_min_storage = minimum_allowed_storage - storage_if_no_hydrogen_produced
    elec_to_maintain_min_storage = production_to_maintain_min_storage / productionFactor
    return max(0, elec_to_maintain_min_storage)

def get_model_output(model_variable):
    for model_variable_type in [ 'gridPower', 'windPower', 'onOff' ]:
        if model_variable.name.startswith(model_variable_type):
            idx = int(model_variable.name[len(model_variable_type):])
            value = model_variable.value()
            return model_variable_type, idx, value
    # TODO handle reaching this point where there was no model output



def calculateCostPerPeriod(timePeriodForecast, lpGridPowerVariable, lpWindPowerVariable):
    gridCost = lpGridPowerVariable * timePeriodForecast.gridPrice
    windCost = lpWindPowerVariable * timePeriodForecast.renewablePrice
    return gridCost + windCost

def calculateMaxConsumptionPerPeriod(config):
    max_production_per_period = config.productionLimits.maxProductionPh * config.range.periodDuration
    max_consumption_per_period = max_production_per_period / config.productionLimits.productionFactor
    return max_consumption_per_period



# run the simulation assuming that the electrolysers are run
#  using only electricity from wind/renewable sources, limited
#  only by:
# - storage capacity of the tanks
# - availability of wind electricity
# - production limit of the electrolysers
def runMaxRenewableSimulation(request):
    periods = request.config.range.periods
    production_factor = request.config.productionLimits.productionFactor
    max_production_per_period = request.config.productionLimits.maxProductionPh * request.config.range.periodDuration

    simulation_output_by_timestamp = list(map(lambda n: {}, range(periods)))
    for i in range(periods):
        forecast = request.forecasts[i]

        # for this simulation we won't use any electricity from the grid
        simulation_output_by_timestamp[i]['gridPower'] = 0

        # how much hydrogen could we generate in this time period
        #  if we used all available wind power?
        production = max(forecast.renewableGeneration * production_factor, max_production_per_period)
        power_used = production / production_factor
        simulation_output_by_timestamp[i]['windPower'] = power_used

        # assume that we run the electrolysers all the time
        #  under this simulation
        simulation_output_by_timestamp[i]['onOff'] = True

    return simulation_output_by_timestamp


def addSimulationResultToOutput(simulation_name, model_output_by_timestamp, periods, period_duration, production_factor, storage_at_simulation_start, max_storage, forecasts, output):
    cumulativeStorage = storage_at_simulation_start
    cumulativeElectricityCost = { 'wind' : 0.0, 'grid' : 0.0 }

    for i in range(periods):
        # how much power does the model say would be optimal for this time period
        modelOutputWindPower = model_output_by_timestamp[i]['windPower']
        modelOutputGridPower = model_output_by_timestamp[i]['gridPower']
        # whether the model says the electrolyser should be on or off for this time period
        modelOutputOnOff     = model_output_by_timestamp[i]['onOff']

        # the cost of electricity to follow the model's recommendation
        modelOutputWindCost = modelOutputWindPower * (period_duration * forecasts[i].renewablePrice)
        modelOutputGridCost = modelOutputGridPower * (period_duration * forecasts[i].gridPrice)

        cumulativeElectricityCost['wind'] += modelOutputWindCost
        cumulativeElectricityCost['grid'] += modelOutputGridCost

        # the amount of hydrogen produced by following the model's recommendation
        hydrogenProducedWind = modelOutputWindPower * production_factor
        hydrogenProducedGrid = modelOutputGridPower * production_factor
        hydrogenProduced = hydrogenProducedWind + hydrogenProducedGrid

        # the amount of hydrogen stored by following the model's recommendation
        changeInStoredHydrogen = hydrogenProduced - forecasts[i].hydrogenDemand
        cumulativeStorage += changeInStoredHydrogen

        # check we haven't produced too much (shouldn't happen when using the
        #  model, but is possible under alternate simulations)
        excess_hydrogen = cumulativeStorage - max_storage
        if excess_hydrogen > 0:
            cumulativeStorage = max_storage
            changeInStoredHydrogen -= excess_hydrogen

        output[i][simulation_name] = {
            'electricityUsage': {
                'wind': modelOutputWindPower,
                'grid': modelOutputGridPower,
                'total': modelOutputWindPower + modelOutputGridPower
            },
            'electricityCost': {
                'wind': modelOutputWindCost,
                'grid': modelOutputGridCost,
                'total': modelOutputWindCost + modelOutputGridCost
            },
            'electricityCostCumulative': {
                'wind': cumulativeElectricityCost['wind'],
                'grid': cumulativeElectricityCost['grid'],
                'total': cumulativeElectricityCost['wind'] + cumulativeElectricityCost['grid']
            },
            'hydrogenProduced': {
                'wind': hydrogenProducedWind,
                'grid': hydrogenProducedGrid,
                'total': hydrogenProducedWind + hydrogenProducedGrid
            },
            'hydrogenInStorage': cumulativeStorage,
            'electrolyserOn': modelOutputOnOff == 1
        }



def runSimulations(request):
    periods = request.config.range.periods
    period_duration = request.config.range.periodDuration
    forecasts = request.forecasts
    minimum_allowed_storage = request.config.storage.minStorageSetPoint
    max_storage = request.config.storage.maxStorage
    storage_at_simulation_start = request.config.storage.initialStorage
    production_factor = request.config.productionLimits.productionFactor
    min_production_rate = request.config.productionLimits.minProductionRate
    max_power_change = request.config.productionLimits.maxPowerChangePh

    # check that we have a valid request
    assert periods == len(forecasts)

    # calculate some limits that will be used by the model
    max_elec_consumption_by_electrolysers = calculateMaxConsumptionPerPeriod(request.config)

    #
    # create the model that will be used to run the "optimal" scenario simulations
    #

    model = LpProblem(name='hydrogen_production')


    #
    # define the variables that the model can vary to find the optimal solution
    #

    # Create variables for power consumption in each time slot in MWh
    gridPower = {i: LpVariable(name=f'gridPower{i}', lowBound=0) for i in range(periods)}
    windPower = {i: LpVariable(name=f'windPower{i}', lowBound=0) for i in range(periods)}

    # on/off variable 0 - if electrolyser off, 1 if on and more than the minimum level is produced
    onOff = {i: LpVariable(name=f'onOff{i}', cat = 'Integer', lowBound=0, upBound=1) for i in range(periods)}


    #
    # specify the goal that the model should be optimising for
    #   (i.e. minimal cost of electricity used to generate the hydrogen)
    #

    # create the objective function, price in £/MHw
    model.setObjective(lpSum(calculateCostPerPeriod(forecasts[i], gridPower[i], windPower[i]) for i in range(periods)))


    #
    # specify the constraints that the model should use
    #

    # define model constraints
    cumulativeHydrogenDemand = 0

    for i in range(periods):
        forecast = forecasts[i]

        # hydrogen demand since the start of the simulation
        cumulativeHydrogenDemand += forecast.hydrogenDemand

        # constraint 1: don't use more wind power than the forecast says will be available
        model += (windPower[i] <= forecast.renewableGeneration, 'Max wind power available ' + str(i))

        # constraint 2: can't consume more electricity than the max usage of the electrolysers per period
        # TODO: original wording was around max hydrogen production - do we need this constraint in the model too? or is this sufficient?
        model += (gridPower[i]+ windPower[i] <= max_elec_consumption_by_electrolysers, 'Max elec consumption ' + str(i))

        # constraint 3: min electricity to consume for hydrogen production this period
        # if we consume less, we will not produce enough hydrogen to meet min storage levels
        min_elec_consumption_to_maintain_min_storage = calculate_elec_needed_to_maintain_min_storage(storage_at_simulation_start, cumulativeHydrogenDemand, minimum_allowed_storage, production_factor)
        model += (lpSum(gridPower[j] + windPower[j] for j in range(i+1)) >=  min_elec_consumption_to_maintain_min_storage , 'Elec to maintain min storage ' + str(i))

        # constraint 4: max electricity to consume for hydrogen production this period
        # if we consume more, we will produce more hydrogen than we can store
        if i < periods - 1:
            max_elec_consumption_storage_constrained = (max_storage - storage_at_simulation_start + cumulativeHydrogenDemand) / production_factor
        else:
             max_elec_consumption_storage_constrained = (cumulativeHydrogenDemand) / production_factor # ensure we end up where we started
        
        model += (lpSum(gridPower[j] + windPower[j] for j in range(i+1)) <= max_elec_consumption_storage_constrained, 'Max elec used given storage limit' + str(i))

        # constraint 5: Ensure power is either 0 or more than the minimum level
        min_elec_consumption_of_electrolysers = max_elec_consumption_by_electrolysers / production_factor * min_production_rate
        model += (gridPower[i] + windPower[i] - min_elec_consumption_of_electrolysers * onOff[i] >= 0, 'Min hydrolyser prod rate'+ str(i))

        # constraint 6: if power is being used, machines must be set to on
        # M is constant large enough to ensure that if power usage > 0 Z = 1
        M = max_elec_consumption_by_electrolysers * 10
        model += (gridPower[i] + windPower[i] -  M * onOff[i] <= 0, 'Set on off'+ str(i))

        # constraint 7: don't change power usage faster than max_power_change
        max_power_change_per_period = max_power_change * period_duration
        # Need to compare with next period, so cannot add for final period (future input data, would be good to have initialProduction value)
        if i+1 < periods:
            model += (gridPower[i] - gridPower[i+1] + windPower[i] - windPower[i+1]<=  max_power_change_per_period, 'Max ramp down of electrolyser power usage ' + str(i))
            model += (gridPower[i] - gridPower[i+1] + windPower[i] - windPower[i+1]>= -max_power_change_per_period, 'Max ramp up of electrolyser power usage  ' + str(i))


    #
    # run the model
    #

    model.solve()

    #
    # initialise output to return
    #

    output = []
    for i in range(periods): output.append({ 'timestamp': request.forecasts[i].timestamp })


    #
    # add simulation results to the output to return
    #

    # re-shape values from the model to let us index them
    #  by timestamp
    model_output_by_timestamp = list(map(lambda n: {}, range(periods)))
    for var in model.variables():
        output_type, time_period_id, value = get_model_output(var)
        model_output_by_timestamp[time_period_id][output_type] = value

    # add the model results to the output
    addSimulationResultToOutput('optimal',
        model_output_by_timestamp,
        periods,
        period_duration,
        production_factor,
        storage_at_simulation_start,
        max_storage,
        forecasts,
        output)

    # add the model status to the output
    model_status = pulp.LpStatus[model.status]
    #TODO: decide where to put this in output

    #
    # generate alternate simulation results
    #
    renewable_simulation = runMaxRenewableSimulation(request)

    addSimulationResultToOutput('hypotheticalWindOnly',
        renewable_simulation,
        periods,
        period_duration,
        production_factor,
        storage_at_simulation_start,
        max_storage,
        forecasts,
        output)


    #
    # final output is ready to return
    #

    return { "simulations": output,
            "statusOfOptimalModel": model_status,
            "units": {
                "electricityUsage": "MWh",
                "electricityCost": "£",
                "electricityCostCumulative": "£",
                "hydrogenProduced": 'm^3',
                "hydrogenInStorage": 'm^3',
                "electrolyserOn": None
            } }
