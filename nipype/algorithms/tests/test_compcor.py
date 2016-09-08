# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import (assert_equal, assert_true, assert_false, skipif,
                            utils)
from nipype.algorithms.compcor import CompCor, TCompCor, ACompCor

import unittest
import mock
import nibabel as nb
import numpy as np
import os
from hashlib import sha1

class TestCompCor(unittest.TestCase):
    ''' Note: Tests currently do a poor job of testing functionality '''

    filenames = {'functionalnii': 'compcorfunc.nii',
                 'masknii': 'compcormask.nii',
                 'components_file': None}

    def setUp(self):
        # setup
        noise = np.fromfunction(self.fake_noise_fun, self.fake_data.shape)
        self.realigned_file = utils.save_toy_nii(self.fake_data + noise,
                                                 self.filenames['functionalnii'])

    def test_compcor(self):
        mask = np.ones(self.fake_data.shape[:3])
        mask[0,0,0] = 0
        mask[0,0,1] = 0
        mask_file = utils.save_toy_nii(mask, self.filenames['masknii'])

        expected_sha1 = 'b0dd7f9ab7ba8f516712eb0204dacc9e397fc6aa'

        ccresult = self.run_cc(CompCor(realigned_file=self.realigned_file,
                                       mask_file=mask_file),
                               expected_sha1)

        accresult = self.run_cc(ACompCor(realigned_file=self.realigned_file,
                                         mask_file=mask_file,
                                         components_file='acc_components_file'),
                                expected_sha1)

        assert_equal(os.path.getsize(ccresult.outputs.components_file),
                     os.path.getsize(accresult.outputs.components_file))

    def test_tcompcor(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file)
        self.run_cc(ccinterface, '12e54c07281a28ac0da3b934dce5c9d27626848a')

    def run_cc(self, ccinterface, expected_components_data_sha1):
        # run
        ccresult = ccinterface.run()

        # assert
        expected_file = ccinterface._list_outputs()['components_file']
        assert_equal(ccresult.outputs.components_file, expected_file)
        assert_true(os.path.exists(expected_file))
        assert_true(os.path.getsize(expected_file) > 0)
        assert_equal(ccinterface.inputs.num_components, 6)

        with open(ccresult.outputs.components_file, 'r') as components_file:
            components_data = [line for line in components_file]
            num_got_components = len(components_data)
            assert_true(num_got_components == ccinterface.inputs.num_components
                        or num_got_components == self.fake_data.shape[3])
            print(str(components_data), "comdata")
            assert_equal(sha1(str(components_data)).hexdigest(), expected_components_data_sha1)
        return ccresult

    def tearDown(self):
        utils.remove_nii(self.filenames.values())

    def fake_noise_fun(self, i, j, l, m):
        return m*i + l - j

    fake_data = np.array([[[[8, 5, 3, 8, 0],
                            [6, 7, 4, 7, 1]],

                           [[7, 9, 1, 6, 5],
                            [0, 7, 4, 7, 7]]],

                          [[[2, 4, 5, 7, 0],
                            [1, 7, 0, 5, 4]],

                           [[7, 3, 9, 0, 4],
                            [9, 4, 1, 5, 0]]]])
