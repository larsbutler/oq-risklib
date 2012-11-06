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

import os, unittest

from risklib import api
from risklib import scenario
from risklib.models import input
from risklib import vulnerability_function
from risklib.tests.utils import vectors_from_csv

THISDIR = os.path.dirname(__file__)

gmv = vectors_from_csv('gmv', THISDIR)

def vf(loss_ratios, covs=(0.0, 0.0, 0.0, 0.0, 0.0)):
    return vulnerability_function.VulnerabilityFunction(
        [0.1, 0.2, 0.3, 0.5, 0.7], loss_ratios, covs, "LN")

class ScenarioRiskTestCase(unittest.TestCase):

    vulnerability_model_mean = dict(
        RM=vf([0.05, 0.1, 0.2, 0.4, 0.8]),
        RC=vf([0.035, 0.07, 0.14, 0.28, 0.56])
        )

    hazard_mean = dict(
        a1=[0.17111044666642075, 0.3091294488722627,
            0.15769192850594427, 0.33418745728229904,
            0.1744414801203893, 0.29182607890936946,
            0.16115560432050713, 0.2822499831821711,
            0.22753947129871863, 0.2900247583738464],
        a3=[0.3051275714154333, 0.2670311789324559,
            0.15943380711124205, 0.2361640051201896,
            0.2885030735639452, 0.244808088235014,
            0.16157066112741528, 0.2395727775322746,
            0.4791639979180004, 0.38630241325610637],
        a2=[0.6040315550126056, 0.33487798185272694,
            0.39260185463612385, 0.367634839907372,
            0.34461255379999045, 0.28035744548676755,
            0.44360919761302703, 0.2418451146800914,
            0.5069824581167889, 0.45975761535464116],
        )

    def test_mean_based(self):
        args_dict = {'seed': None,
                     'correlation_type': None,
                     'insured': False}

        calculator = api.ScenarioRisk(
            self.vulnerability_model_mean, args_dict)

        asset_output = calculator(
            input.Asset("a1", "RM", 3000, None),
            self.hazard_mean["a1"])

        self.assertAlmostEqual(440.147078317589,
            asset_output.mean)

        self.assertAlmostEqual(182.615976701858,
            asset_output.standard_deviation)

        asset_output = calculator(
            input.Asset("a3", "RM", 1000, None),
            self.hazard_mean["a3"])

        self.assertAlmostEqual(180.717534009275,
            asset_output.mean)

        self.assertAlmostEqual(92.2122644809969,
            asset_output.standard_deviation)

        asset_output = calculator(
            input.Asset("a2", "RC", 2000, None),
            self.hazard_mean["a2"])

        self.assertAlmostEqual(432.225448142534,
            asset_output.mean)

        self.assertAlmostEqual(186.864456949986,
            asset_output.standard_deviation)

        total_losses = scenario.aggregate_losses(
            [calculator.aggregate_losses])

        self.assertAlmostEqual(246.62, total_losses[1], places=2)
        self.assertAlmostEqual(1053.09, total_losses[0], places=2)

    def test_sample_based(self):
        vulnerability_model = dict(
            RM=vf([0.05, 0.1, 0.2, 0.4, 0.8], [0.05, 0.06, 0.07, 0.08, 0.09]),
            RC=vf([0.035, 0.07, 0.14, 0.28, 0.56], [0.1, 0.2, 0.3, 0.4, 0.5]),
            )

        args_dict = {'seed': 37,
                     'correlation_type': None,
                     'insured': False}

        calculator = api.ScenarioRisk(vulnerability_model, args_dict)

        asset_output = calculator(
            input.Asset("a1", "RM", 3000, None), gmv.a1)

        self.assertAlmostEqual(521.885458891, asset_output.mean,
            delta=0.05 * 521.885458891)

        self.assertTrue(asset_output.standard_deviation > 244.825980356)

        asset_output = calculator(
            input.Asset("a3", "RM", 1000, None), gmv.a3)

        self.assertAlmostEqual(200.54874638, asset_output.mean,
            delta=0.05 * 200.54874638)

        self.assertTrue(asset_output.standard_deviation > 94.2302991022)

        asset_output = calculator(
            input.Asset("a2", "RC", 2000, None), gmv.a2)

        self.assertAlmostEqual(510.821363253, asset_output.mean,
            delta=0.05 * 510.821363253)

        self.assertTrue(asset_output.standard_deviation > 259.964152622)

        total_losses = scenario.aggregate_losses(
            [calculator.aggregate_losses])

        self.assertAlmostEqual(1233.26,
            total_losses[0], delta=0.05 * 1233.26)

        self.assertTrue(total_losses[1] > 443.63)

    def test_insured_losses_mean(self):
        args_dict = {'correlation_type': None,
                     'seed': None,
                     'insured': True}

        calculator = api.ScenarioRisk(
            self.vulnerability_model_mean, args_dict)

        asset_output = calculator(
            input.Asset("a1", "RM", 3000, None,
            deductible=300, ins_limit=600),
            self.hazard_mean["a1"])

        self.assertAlmostEqual(327.492087529, asset_output.mean)

        self.assertAlmostEqual(288.47906994,
            asset_output.standard_deviation)

        asset_output = calculator(
            input.Asset("a3", "RM", 1000, None,
            deductible=100, ins_limit=300),
            self.hazard_mean["a3"])

        self.assertAlmostEqual(156.750910806, asset_output.mean)

        self.assertAlmostEqual(100.422061776,
            asset_output.standard_deviation)

        asset_output = calculator(
            input.Asset("a2", "RC", 2000, None,
            deductible=350, ins_limit=800),
            self.hazard_mean["a2"])

        self.assertAlmostEqual(314.859579324, asset_output.mean)

        self.assertAlmostEqual(293.976254984,
            asset_output.standard_deviation)

        total_losses = scenario.aggregate_losses(
            [calculator.aggregate_losses])

        self.assertAlmostEqual(799.102578, total_losses[0], places=5)
        self.assertAlmostEqual(382.148808, total_losses[1], places=5)
