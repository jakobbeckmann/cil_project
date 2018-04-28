import glob
import os

import keras
import matplotlib.image as mpimg
import numpy as np
import sys, traceback

class PatchTestImageGenerator:
    def __init__(self, path_to_images, path_to_groundtruth, pad=28, patch_size=16, context_padding=28):
        data_files = glob.glob(os.path.join(path_to_images, "*.png"))
        mask_files = glob.glob(os.path.join(path_to_groundtruth, "*.png"))
        image_count = len(data_files)
        first = mpimg.imread(data_files[0])

        data_set = np.empty((image_count,
                             first.shape[0] + 2 * pad,
                             first.shape[1] + 2 * pad,
                             first.shape[2]))
        verifier_set = np.empty((image_count, first.shape[0], first.shape[1]))

        for idx, (file, mask_file) in enumerate(zip(data_files, mask_files)):
            data_set[idx] = np.pad(mpimg.imread(file), ((pad, pad), (pad, pad), (0, 0)), mode="reflect")
            verifier_set[idx] = mpimg.imread(mask_file)

        self.data_set = data_set
        self.verifier_set = verifier_set

        self.window_size = patch_size + 2 * context_padding
        self.patch_size = patch_size
        self.context_padding = context_padding

        print('PatchImageGenerator initialized with {} pictures'.format(image_count))

    def check_dimensions_patch_with_img(self, w_img, h_img):
        patch_size = self.patch_size
        check_result = w_img/patch_size == 0 and h_img/patch_size
        return check_result

    def get_test_patches_from_image(self, data_img):
        window_size = self.window_size
        patch_size = self.patch_size
        context_padding = self.context_padding

        width_image, height_image = data_img.shape
        check_result = self.check_dimensions_patch_with_img(width_image, height_image)
        
        if not check_result:
            print("The width of the image ",width_image," and the height of the image", height_image,
                   " are incompatible with patch size ", patch_size)
            traceback.print_exc(file=sys.stdout)
            sys.exit(0)
        
        patches_over_width = width_image/patch_size
        patches_over_height = height_image/patch_size
        
        """Test patches:
            from the bottom to top w.r.t the image height, 
            from the left to the right w.r.t the image width
        """
        img_patches = []
        for patch_h_idx in range(patches_over_height):
            
            height_patch = patch_h_idx * patch_size
            for patch_w_idx in range(patches_over_width):

                width_patch = patch_w_idx * patch_size
            
                img_patches.append(img[patch_w_idx*patch_size:patch_w_idx*patch_size+patch_size, patch_h_idx*patch_size:patch_h_idx*patch_size+patch_size, :])

        return np.asarray(img_patches)



    def generate_test_patches(self, batch_size=100, four_dim=False):
        window_size = self.window_size
        patch_size = self.patch_size
        context_padding = self.context_padding
        while True:

            for img in self.data_set:
                img_patches = self.get_test_patches_from_image(img)

                if four_dim:
                    patch_idx = 0;
                    for patch in img_patches:
                        img_patches[patch_idx] = patch.reshape(batch_size, self.window_size, self.window_size, 3, 1)
                        patch_idx = patch_idx + 1

                yield img_patches

    def input_dim(self, four_dim=False):
        if four_dim:
            return self.window_size, self.window_size, 3, 1
        return self.window_size, self.window_size, 3