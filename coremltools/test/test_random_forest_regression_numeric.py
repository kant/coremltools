# Copyright (c) 2017, Apple Inc. All rights reserved.
#
# Use of this source code is governed by a BSD-3-clause license that can be
# found in the LICENSE.txt file or at https://opensource.org/licenses/BSD-3-Clause

import unittest
import numpy as np
import pandas as pd
import os
from coremltools._deps import HAS_SKLEARN
from coremltools.models.utils import evaluate_regressor
from nose.plugins.attrib import attr

if HAS_SKLEARN:
    from sklearn.ensemble import RandomForestRegressor
    from coremltools.converters import sklearn as skl_converter

@unittest.skipIf(not HAS_SKLEARN, 'Missing sklearn. Skipping tests.')
class RandomForestRegressorBostonHousingScikitNumericTest(unittest.TestCase):
    """
    Unit test class for testing scikit-learn converter and running both models
    """
    @classmethod
    def setUpClass(self):
        """
        Set up the unit test by loading the dataset and training a model.
        """
        from sklearn.datasets import load_boston

        # Load data and train model
        scikit_data = load_boston()
        self.scikit_data = scikit_data
        self.X = scikit_data.data.astype('f').astype('d') ## scikit-learn downcasts data
        self.target = scikit_data.target
        self.feature_names = scikit_data.feature_names
        self.output_name = 'target'

    def _check_metrics(self, metrics, params = {}):
        """
        Check the metrics
        """
        self.assertAlmostEquals(metrics['rmse'], 0.0, delta = 1e-5,
                msg = 'Failed case %s. Results %s' % (params, metrics))
        self.assertAlmostEquals(metrics['max_error'], 0.0, delta = 1e-5,
                msg = 'Failed case %s. Results %s' % (params, metrics))

    def _train_convert_evaluate(self, **scikit_params):
        """
        Train a scikit-learn model, convert it and then evaluate it with CoreML
        """
        scikit_model = RandomForestRegressor(random_state = 1, **scikit_params)
        scikit_model.fit(self.X, self.target)

        # Convert the model
        spec = skl_converter.convert(scikit_model, self.feature_names, self.output_name)

        # Get predictions
        df = pd.DataFrame(self.X, columns=self.feature_names)
        df['prediction'] = scikit_model.predict(self.X)

        # Evaluate it
        metrics = evaluate_regressor(spec, df, verbose = False)
        return metrics

    def test_boston_housing_simple_regression(self):
        metrics = self._train_convert_evaluate()
        self._check_metrics(metrics)

    def test_boston_housing_float_double_corner_case(self):
        metrics = self._train_convert_evaluate(max_depth = 13)
        self._check_metrics(metrics)

    @attr('slow')
    def test_boston_housing_parameter_stress_test(self):

        ## These are all the options in decision tree regression of scikit-learn
        options = dict(
            criterion = ['mse'],
            n_estimators = [1, 5, 10],
            max_depth = [1, 5],
            min_samples_split = [2, 10, 0.5],
            min_samples_leaf = [1, 5],
            min_weight_fraction_leaf = [0.0, 0.5],
            max_leaf_nodes = [None, 20],
            min_impurity_decrease = [1e-07, 0.1, 0.0],
        )

        # Make a cartesian product of all options
        import itertools
        product = itertools.product(*options.values())
        args = [dict(zip(options.keys(), p)) for p in product]

        print("Testing a total of %s cases. This could take a while" % len(args))
        for it, arg in enumerate(args):
            metrics = self._train_convert_evaluate(**arg)
            self._check_metrics(metrics, arg)
