import pydantic
import unittest
from app.lpmodel import runSimulations, calculate_elec_needed_to_maintain_min_storage
from app.electricity import Forecast, SimulationOutput


class LpModelTest(unittest.TestCase):

    def test_model_24hours(self):
        # run the LP model
        input = pydantic.parse_file_as(path='app/test/24-hours/sample-input.json', type_=Forecast)
        output = runSimulations(input)
        # check the output matches the expectations
        expected_output = pydantic.parse_file_as(path='app/test/24-hours/expected-output.json', type_=SimulationOutput)
        assert expected_output.dict() == output


    def test_model_48hours(self):
        # run the LP model
        input = pydantic.parse_file_as(path='app/test/48-hours/sample-input.json', type_=Forecast)
        output = runSimulations(input)
        # check the output matches the expectations
        expected_output = pydantic.parse_file_as(path='app/test/48-hours/expected-output.json', type_=SimulationOutput)
        assert expected_output.dict() == output


    def test_model_1hour(self):
        input = pydantic.parse_file_as(path='app/test/60-minutes/sample-input.json', type_=Forecast)
        output = runSimulations(input)
        # check the output matches the expectations
        expected_output = pydantic.parse_file_as(path='app/test/60-minutes/expected-output.json', type_=SimulationOutput)
        assert expected_output.dict() == output


    def test_model_1hour_no_wind(self):
        input = pydantic.parse_file_as(path='app/test/24-hours/sample-input.json', type_=Forecast)
        for item in input.forecasts:
            item.renewableGeneration = 0

        output = runSimulations(input)
        for result in output['simulations']:
            assert result['optimal']['electricityUsage']['wind'] == 0
            assert result['optimal']['electricityCost']['wind'] == 0


    def test_model_single_period(self):
        input = pydantic.parse_file_as(path='app/test/30-minutes/sample-input.json', type_=Forecast)
        output = runSimulations(input)
        # check the output matches the expectations
        expected_output = pydantic.parse_file_as(path='app/test/30-minutes/expected-output.json', type_=SimulationOutput)
        assert expected_output.dict() == output



class CalculateElecNeededTest(unittest.TestCase):

    def test_calculate_elec_needed_to_maintain_min_storage(self):
        # empty when we start
        storage_at_start = 0
        # we need 100 m^3 of hydrogen
        demand = 100
        # we need to keep at least 10 m^3 in storage
        min_storage = 10

        output = calculate_elec_needed_to_maintain_min_storage(storage_at_start, demand, min_storage, 1)

        # we should produce at least 110 (100 to meet the demand, and an extra 10 for storage)
        assert 110 == output


    def test_calculate_no_elec_needed_to_maintain_min_storage(self):
        # more than enough when we start
        storage_at_start = 500
        # we need 100 m^3 of hydrogen
        demand = 100
        # we need to keep at least 10 m^3 in storage
        min_storage = 10

        output = calculate_elec_needed_to_maintain_min_storage(storage_at_start, demand, min_storage, 1)

        # there is enough storage to meet the demand, without taking us below the min limit
        assert 0 == output


    def test_calculate_elec_needed_to_maintain_min_storage_with_no_demand(self):
        # more than enough when we start
        storage_at_start = 500
        # no hydrogen needed
        demand = 0
        # we need to keep at least 10 m^3 in storage
        min_storage = 10

        output = calculate_elec_needed_to_maintain_min_storage(storage_at_start, demand, min_storage, 1)

        # there is enough storage to meet the demand, without taking us below the min limit
        assert 0 == output

