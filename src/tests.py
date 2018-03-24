#!/usr/bin/env python3

"""Tester module. This should implement unit tests for any important functionalities."""

import os, sys
import unittest
import glob, logging
import numpy as np

import utility
from models import cnn_lr_d

file_path = os.path.dirname(os.path.abspath(__file__))

class TestUtilities(unittest.TestCase):
    """Class testing all utility functions."""

    @unittest.skipIf(len(glob.glob(os.path.join(file_path,
                                                "../assets/testing/test_img*.png"))) != 1,
                     "Too many test files in folder. Please ensure that the augmentation" +
                     " was not already run")
    def test_augment_img_set(self):
        """Tests the image augmentation"""
        utility.augment_img_set(os.path.join(file_path, "../assets/testing/"))
        img_count = len([1 for file in glob.glob(os.path.join(file_path,
                                                              "../assets/testing/test_img*.png"))])
        self.assertEqual(img_count, 8, msg="Not correct number of images generated by augmenting " +
                                           " test_img.png file")

    def test_generate_patches_with_pad(self):
        """Tests the patch generating function with padding"""
        # Setup
        img_fail = np.array([1, 2, 3])
        img_2d = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        img_3d = np.array([[[1, 1, 1], [2, 2, 2], [3, 3, 3]],
                           [[4, 4, 4], [5, 5, 5], [6, 6, 6]],
                           [[7, 7, 7], [8, 8, 8], [9, 9, 9]]])

        # Check for fail
        with self.assertRaises(TypeError):
            utility.generate_patches_with_pad(img_fail, 2, 2, 0)
        # Check for grayscale image
        patch_list_2d = [[[1]], [[2]], [[3]], [[4]], [[5]], [[6]], [[7]], [[8]], [[9]]]
        patch_list_2d_res = utility.generate_patches_with_pad(img_2d, 1, 1, 0)
        self.assertEqual(np.testing.assert_equal(patch_list_2d, patch_list_2d_res), None)
        # Check for RGB image
        patch_list_3d = [
            np.array([[[5,5,5], [4,4,4], [5,5,5]],
                      [[2,2,2], [1,1,1], [2,2,2]],
                      [[5,5,5], [4,4,4], [5,5,5]]]),
            np.array([[[4,4,4], [5,5,5], [6,6,6]],
                      [[1,1,1], [2,2,2], [3,3,3]],
                      [[4,4,4], [5,5,5], [6,6,6]]]),
            np.array([[[5,5,5], [6,6,6], [5,5,5]],
                      [[2,2,2], [3,3,3], [2,2,2]],
                      [[5,5,5], [6,6,6], [5,5,5]]]),
            np.array([[[2,2,2], [1,1,1], [2,2,2]],
                      [[5,5,5], [4,4,4], [5,5,5]],
                      [[8,8,8], [7,7,7], [8,8,8]]]),
            np.array([[[1,1,1], [2,2,2], [3,3,3]],
                      [[4,4,4], [5,5,5], [6,6,6]],
                      [[7,7,7], [8,8,8], [9,9,9]]]),
            np.array([[[2,2,2], [3,3,3], [2,2,2]],
                      [[5,5,5], [6,6,6], [5,5,5]],
                      [[8,8,8], [9,9,9], [8,8,8]]]),
            np.array([[[5,5,5], [4,4,4], [5,5,5]],
                      [[8,8,8], [7,7,7], [8,8,8]],
                      [[5,5,5], [4,4,4], [5,5,5]]]),
            np.array([[[4,4,4], [5,5,5], [6,6,6]],
                      [[7,7,7], [8,8,8], [9,9,9]],
                      [[4,4,4], [5,5,5], [6,6,6]]]),
            np.array([[[5,5,5], [6,6,6], [5,5,5]],
                      [[8,8,8], [9,9,9], [8,8,8]],
                      [[5,5,5], [6,6,6], [5,5,5]]])
        ]
        patch_list_3d_res = utility.generate_patches_with_pad(img_3d, 1, 1, 1)
        self.assertEqual(np.testing.assert_equal(patch_list_3d, patch_list_3d_res), None)

    def test_image_set_loader(self):
        """Test the image set loader utility function"""
        utility.load_training_set(os.path.join(file_path,
                                               os.path.normpath("../assets/training/data")),
                                  28,
                                  suppress_output=True)

class TestModels(unittest.TestCase):
    """Class testing the models."""

    def test_model_generation(self):
        """Test the model generations"""
        with self.assertRaises(ValueError):
            cnn_model1 = cnn_lr_d.Model(os.path.join(file_path, "../assets/training/data"),
                                        load_images=False)




def run():
    unittest.main(module="tests")
