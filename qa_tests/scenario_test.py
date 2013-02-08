# coding=utf-8
# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake Risklib is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# OpenQuake Risklib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with OpenQuake Risklib. If not, see
# <http://www.gnu.org/licenses/>.

import os
import unittest

from oqrisklib import api
from oqrisklib import scientific
from oqrisklib.tests.utils import vectors_from_csv

THISDIR = os.path.dirname(__file__)

gmv = vectors_from_csv('gmv', THISDIR)


def vf(loss_ratios, covs=(0.0, 0.0, 0.0, 0.0, 0.0)):
    return scientific.VulnerabilityFunction(
        [0.1, 0.2, 0.3, 0.5, 0.7], loss_ratios, covs, "LN")


class ScenarioTestCase(unittest.TestCase):

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
        calculator = api.Scenario(
            self.vulnerability_model_mean["RM"], None, None)

        [asset_output_a1, asset_output_a3] = calculator(
            [scientific.Asset(3000), scientific.Asset(1000)],
            [self.hazard_mean["a1"], self.hazard_mean["a3"]])

        self.assertAlmostEqual(440.147078317589, asset_output_a1.mean)

        self.assertAlmostEqual(182.615976701858,
                               asset_output_a1.standard_deviation)

        self.assertAlmostEqual(180.717534009275, asset_output_a3.mean)

        self.assertAlmostEqual(92.2122644809969,
                               asset_output_a3.standard_deviation)

        calculator.vulnerability_function = self.vulnerability_model_mean["RC"]
        [asset_output_a2] = calculator(
            [scientific.Asset(2000)], [self.hazard_mean["a2"]])

        self.assertAlmostEqual(432.225448142534, asset_output_a2.mean)

        self.assertAlmostEqual(186.864456949986,
                               asset_output_a2.standard_deviation)

    def test_sample_based(self):
        vulnerability_model = dict(
            RM=vf([0.05, 0.1, 0.2, 0.4, 0.8], [0.05, 0.06, 0.07, 0.08, 0.09]),
            RC=vf([0.035, 0.07, 0.14, 0.28, 0.56], [0.1, 0.2, 0.3, 0.4, 0.5]),
        )

        calculator = api.Scenario(vulnerability_model['RM'], seed=37)

        [asset_output_a1, asset_output_a3] = calculator(
            [scientific.Asset(3000), scientific.Asset(1000)],
            [gmv.a1, gmv.a3])

        self.assertAlmostEqual(521.885458891, asset_output_a1.mean,
                               delta=0.05 * 521.885458891)
        self.assertTrue(asset_output_a1.standard_deviation > 244.825980356)

        self.assertAlmostEqual(200.54874638, asset_output_a3.mean,
                               delta=0.05 * 200.54874638)

        self.assertTrue(asset_output_a3.standard_deviation > 94.2302991022)

        calculator.vulnerability_function = vulnerability_model["RC"]
        calculator.vulnerability_function.init_distribution(seed=37)

        [asset_output_a2] = calculator([scientific.Asset(2000)], [gmv.a2])

        self.assertAlmostEqual(510.821363253, asset_output_a2.mean,
                               delta=0.05 * 510.821363253)

        self.assertTrue(asset_output_a2.standard_deviation > 259.964152622)
