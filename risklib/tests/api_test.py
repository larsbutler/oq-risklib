# coding=utf-8
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import mock
import unittest

from risklib.tests import utils
from risklib.models import input, output
from risklib import api, curve, vulnerability_function


class ComputeOnSitesTestCase(unittest.TestCase):

    def test_multiple_sites(self):
        asset = input.Asset("a1", None, None, None)
        sites = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)
        assets_getter = mock.Mock(return_value=[asset])

        list(api.compute_on_sites(sites,
            assets_getter, hazard_getter, calculator))

        expected_calls = [(((1.0, 1.0),), {}), (((2.0, 2.0),), {}),
            (((3.0, 3.0),), {})]

        self.assertEquals(expected_calls, assets_getter.call_args_list)
        self.assertEquals(expected_calls, hazard_getter.call_args_list)

        self.assertEquals([((asset, 1.0), {})] * 3,
            calculator.call_args_list)

    def test_multiple_assets_per_site(self):
        sites = [(1.0, 1.0)]

        assets = [
            input.Asset("a1", None, None, None),
            input.Asset("a2", None, None, None),
            input.Asset("a3", None, None, None),
        ]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)
        assets_getter = mock.Mock(return_value=assets)

        list(api.compute_on_sites(sites,
            assets_getter, hazard_getter, calculator))

        expected_calls = [((assets[0], 1.0), {}), ((assets[1], 1.0), {}),
            ((assets[2], 1.0), {})]

        self.assertEquals(expected_calls, calculator.call_args_list)


class ComputeOnAssetsTestCase(unittest.TestCase):

    def test_compute_on_assets(self):
        assets = [
            input.Asset("a1", None, None, (1.0, 1.0)),
            input.Asset("a2", None, None, (2.0, 2.0)),
            input.Asset("a3", None, None, (3.0, 3.0)),
        ]

        calculator = mock.Mock()
        hazard_getter = mock.Mock(return_value=1.0)

        list(api.compute_on_assets(assets, hazard_getter, calculator))

        expected_calls = [(((1.0, 1.0),), {}), (((2.0, 2.0),), {}),
            (((3.0, 3.0),), {})]

        self.assertEquals(expected_calls, hazard_getter.call_args_list)

        expected_calls = [((assets[0], 1.0), {}), ((assets[1], 1.0), {}),
            ((assets[2], 1.0), {})]

        self.assertEquals(expected_calls, calculator.call_args_list)


class ConditionalLossesTestCase(unittest.TestCase):

    def test_conditional_losses_calculator(self):
        asset = input.Asset("a1", None, None, None)
        asset_output = output.ClassicalOutput(
            asset, [(2.0, 2.0)], [(1.0, 1.0)], None)

        loss_curve_calculator = mock.Mock(return_value=asset_output)

        with mock.patch("risklib.classical._conditional_losses") as stub:
            stub.return_value = {0.1: 0.5, 0.2: 0.5}

            args_dict = {'conditional_loss_poes': [0.1, 0.2]}

            asset_output = api.conditional_losses(
                loss_curve_calculator, args_dict    )(asset, 1.0)

            loss_curve_calculator.assert_called_with(asset, 1.0)

            expected_output = output.ClassicalOutput(
                asset, [(2.0, 2.0)], [(1.0, 1.0)], {0.1: 0.5, 0.2: 0.5})

            # as output we have the output from the given loss curve
            # calculator, plus the conditional losses
            self.assertEquals(expected_output, asset_output)


class ClassicalCalculatorTestCase(unittest.TestCase):

    def test_classical_calculator(self):
        hazard_curve = [(0.1, 0.5), (0.2, 0.6)]
        asset = input.Asset("a1", "RC", 1.0, None)

        function = vulnerability_function.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        vulnerability_model = {"RC": function}
        args_dict = {'steps': 10}
        asset_output = api.Classical(vulnerability_model, args_dict)(asset,
            hazard_curve)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.loss_curve)
        self.assertIsNotNone(asset_output.loss_ratio_curve)


class ScenarioDamageCalculatorTestCase(unittest.TestCase):

    def test_scenario_damage_calculator(self):
        fragility_model = input.FragilityModel("discrete",
            [0.1, 0.2], ["LS1", "LS2"])

        fragility_function = input.FragilityFunctionDiscrete(
            fragility_model, [0.8, 0.7], 1)

        asset = input.Asset("a1", "RC", None, None, number_of_units=1.0)

        calculator = api.ScenarioDamage(fragility_model,
            {"RC": [fragility_function]})

        asset_output = calculator(asset, [0.11, 0.12, 0.13])

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.collapse_map)
        self.assertIsNotNone(asset_output.damage_distribution_asset)
        self.assertIsNotNone(calculator.damage_distribution_by_taxonomy)


class BCRCalculatorTestCase(unittest.TestCase):

    def test_bcr_calculator(self):
        hazard_curve = [(0.1, 0.5), (0.2, 0.6)]
        asset = input.Asset("a1", "RC", 1.0, None, retrofitting_cost=1.0)

        function = vulnerability_function.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        vulnerability_model = {"RC": function}
        vulnerability_model_retrofitted = {"RC": function}
        args_dict = {'interest_rate': 1.0,
                     'asset_life_expectancy': 1.0,
                     'steps': 10}
        asset_output = (api.bcr(vulnerability_model,
            vulnerability_model_retrofitted, api.Classical, args_dict)
            (asset, hazard_curve))

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.bcr)
        self.assertIsNotNone(asset_output.eal_original)
        self.assertIsNotNone(asset_output.eal_retrofitted)


class ProbabilisticEventBasedCalculatorTestCase(unittest.TestCase):

    def test_event_based_calculator(self):
        asset = input.Asset("a1", "RC", 1.0, None)
        hazard = {"IMLs": [0.11, 0.12, 0.13], "TSES": 1, "TimeSpan": 50}

        function = vulnerability_function.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        vulnerability_model = {"RC": function}

        args_dict = {'loss_histogram_bins': 10,
                     'seed': 37,
                     'correlation_type': "perfect"}

        asset_output = api.ProbabilisticEventBased(
            vulnerability_model, args_dict)(asset, hazard)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.losses)
        self.assertIsNotNone(asset_output.loss_curve)
        self.assertIsNotNone(asset_output.loss_ratio_curve)


class InsuredLossesTestCase(unittest.TestCase):

    def test_insured_losses_calculator(self):
        asset = input.Asset("a1", "RC", 1.0, None)
        hazard = {"IMLs": [0.11, 0.12, 0.13], "TSES": 1, "TimeSpan": 50}

        asset_output = utils.new(
            output.ProbabilisticEventBasedOutput,
            losses=[0.5, 0.5, 0.5])

        losses_calculator = mock.Mock(return_value=asset_output)

        with mock.patch(
            "risklib.insured_loss._compute_insured_losses") as stub:
            stub.return_value = [0.5, 0.5, 0.5]

            asset_output = api.insured_losses(losses_calculator)(asset, hazard)
            losses_calculator.assert_called_with(asset, hazard)

            # as output we have the output from the given losses
            # calculator, plus the insured losses
            self.assertEquals([0.5, 0.5, 0.5], asset_output.insured_losses)


class InsuredCurvesTestCase(unittest.TestCase):

    def test_insured_curves_calculator(self):
        hazard = {"IMLs": [0.11, 0.12, 0.13]}
        asset = input.Asset("a1", "RC", 1.0, None)

        function = vulnerability_function.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        vulnerability_model = {"RC": function}

        asset_output = utils.new(
            output.ProbabilisticEventBasedOutput,
            insured_losses=[0.5, 0.5, 0.5])

        insured_losses_calculator = mock.Mock(return_value=asset_output)

        with mock.patch(
            "risklib.insured_loss._compute_insured_loss_ratio_curve") as stub:

            insured_loss_ratio_curve = curve.Curve(
                [(0.5, 1.0), (0.5, 1.0), (0.5, 1.0)])

            stub.return_value = insured_loss_ratio_curve

            args_dict = {'loss_histogram_bins': 10,
                         'seed': 37,
                         'correlation_type': "perfect"}

            asset_output = api.insured_curves(vulnerability_model,
                insured_losses_calculator, args_dict)(asset, hazard)

            insured_losses_calculator.assert_called_with(asset, hazard)

            # as output we have the output from the given insured losses
            # calculator, plus the insured loss ratio and loss curves
            self.assertEquals(insured_loss_ratio_curve,
                asset_output.insured_loss_ratio_curve)

            # the loss curve is equal to the loss ratio curve since the
            # asset value is 1.0
            self.assertEquals(insured_loss_ratio_curve,
                asset_output.insured_loss_curve)


class ScenarioRiskCalculatorTestCase(unittest.TestCase):

    def test_scenario_risk_calculator(self):
        hazard = [0.11, 0.12, 0.13]
        asset = input.Asset("a1", "RC", 1.0, None,
            ins_limit=1.0, deductible=1.0)

        function = vulnerability_function.VulnerabilityFunction(
            [0.1, 0.2], [1.0, 0.5], [0.0, 0.0], "LN")

        vulnerability_model = {"RC": function}

        args_dict = {'seed': 37,
                     'correlation_type': "perfect",
                     'insured': False}

        asset_output = api.ScenarioRisk(
            vulnerability_model, args_dict)(asset, hazard)

        self.assertEquals(asset, asset_output.asset)

        # here we just verify the outputs are stored,
        # because the scientific logic is tested elsewhere
        self.assertIsNotNone(asset_output.mean)
        self.assertIsNotNone(asset_output.standard_deviation)

        args_dict['seed'] = True

        # same, but with an insured calculator
        asset_output = api.ScenarioRisk(
            vulnerability_model, args_dict)(asset, hazard)

        self.assertEquals(asset, asset_output.asset)

        self.assertIsNotNone(asset_output.mean)
        self.assertIsNotNone(asset_output.standard_deviation)
