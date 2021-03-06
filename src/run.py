#!/usr/bin/env python3

import argparse
import datetime
import time

from generators.ImageToPatchGenerator import ImageToPatchGenerator
from generators.PatchTestImageGenerator import PatchTestImageGenerator
from generators.PatchTrainImageGenerator import PatchTrainImageGenerator
from models import cnn_lr_d, u_net_pixel_to_patch
from models import predict_on_tests
from visualization import *


def _setup_argparser():
    """Sets up the argument parser and returns the arguments.

    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description="Control program to launch all actions related to"
                                                 " this project.")

    parser.add_argument("-m", "--model", action="store",
                        choices=["cnn_lr_d", "u_net", "u_net_dropout"],
                        default="u_net_dropout",
                        type=str,
                        help="the CNN model to be used, defaults to u_net")
    parser.add_argument("-t", "--train",
                        help="train the given CNN",
                        action="store_true")
    parser.add_argument("-tr", "--train_resume",
                        help="continue training the given CNN",
                        action="store_true")
    parser.add_argument("-d", "--data",
                        help="path to the data to use (prediction)",
                        action="store",
                        default=os.path.join(properties["TEST_DIR"], "data"),
                        type=str)
    parser.add_argument("-p", "--predict",
                        help="predict on a test set given the CNN",
                        action="store_true")
    parser.add_argument("-vis", "--visualize",
                        help="visualize prediction of an image given its id",
                        action="store")

    args, unknown = parser.parse_known_args()

    return args


def get_latest_submission():
    path_submission = get_latest_model()
    submissions = []
    submissions += [each for each in os.listdir(path_submission) if each.endswith('.csv')]

    if not len(submissions) == 0:

        timestamps = []
        for sub_idx in range(len(submissions)):
            end_ts = submissions[sub_idx].index(".csv") - 1
            start_ts = [x.isdigit() for x in submissions[sub_idx]].index(True)
            timestamps.append(int(submissions[sub_idx][start_ts:end_ts]))
        max_ts_idx = timestamps.index(max(timestamps))
        latest_submission = submissions[max_ts_idx]
    else:
        print("[INFO] No submission csv file for: ", path_submission)
        sys.exit(1)

    print("[INFO] Retrieving last submission in: ", os.path.join(path_submission, latest_submission))

    return os.path.join(path_submission, latest_submission)


def get_latest_model():
    """Returns the latest directory of the model specified in the arguments.

    Returns:
        (path) a path to the directory.
    """
    if not os.path.exists(os.path.join(properties["SRC_DIR"], "../trained_models", args.model)):
        print("[INFO] No trained model {} exists.".format(args.model))
        sys.exit(1)

    res = os.path.join(properties["SRC_DIR"], "../trained_models", args.model)
    all_runs = [os.path.join(res, o) for o in os.listdir(res) if os.path.isdir(os.path.join(res, o))]
    res = max(all_runs, key=os.path.getmtime)

    return res


def get_submission_filename():
    """
    Returns:
        (path to directory) + filename of the submission file.
    """
    ts = int(time.time())
    submission_filename = "submission_" + str(args.model) + "_" + str(ts) + ".csv"
    submission_path_filename = os.path.join(get_latest_model(), submission_filename)

    return submission_path_filename


###########################################################################################
# RUN.PY actions.
###########################################################################################
if __name__ == "__main__":
    file_path = os.path.dirname(os.path.abspath(__file__))
    args = _setup_argparser()

    if args.train:
        properties["OUTPUT_DIR"] = os.path.normpath(
            os.path.join(properties["SRC_DIR"],
                         "../trained_models/",
                         args.model,
                         datetime.datetime.now().strftime(r"%Y-%m-%d[%Hh%M]")))
        try:
            os.makedirs(properties["OUTPUT_DIR"])
        except OSError:
            pass
    elif args.train_resume or args.predict:
        properties["OUTPUT_DIR"] = get_latest_model()
        properties["LOG_DIR"] = os.path.join(properties["OUTPUT_DIR"], "logs")
    else:
        properties["OUTPUT_DIR"] = os.path.normpath("..")

    properties["LOG_DIR"] = os.path.join(properties["OUTPUT_DIR"], "logs")

    if args.train:
        if args.model == "cnn_lr_d":
            train_generator = PatchTrainImageGenerator(os.path.join(properties["TRAIN_DIR_400"], "data"),
                                                       os.path.join(properties["TRAIN_DIR_400"], "verify"))
            model = cnn_lr_d.CnnLrD(train_generator)
            model.train()
        elif args.model == "u_net":
            generator = ImageToPatchGenerator(os.path.join(properties["TRAIN_DIR_608"]),
                                              os.path.join(properties["TEST_DIR"]), 500, 200, True)
            model = u_net_pixel_to_patch.UNet(generator, None)
            model.train()
        elif args.model == "u_net_dropout":
            generator = ImageToPatchGenerator(os.path.join(properties["TRAIN_DIR_608"]),
                                              os.path.join(properties["TEST_DIR"]), 500, 200, True)
            model = u_net_pixel_to_patch.UNet(generator, None, type="dropout")
            model.train()

    elif args.train_resume:

        model = None
        if args.model == "cnn_lr_d":
            train_generator = PatchTrainImageGenerator(os.path.join(properties["TRAIN_DIR_400"], "data"),
                                                       os.path.join(properties["TRAIN_DIR_400"], "verify"))
            model = cnn_lr_d.CnnLrD(train_generator,
                                    path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"))
            model.train()

        elif args.model == "u_net":
            generator = ImageToPatchGenerator(os.path.join(properties["TRAIN_DIR_608"]),
                                              os.path.join(properties["TEST_DIR"]), 500, 200, True)

            print("[INFO] Path ", properties["OUTPUT_DIR"])
            model = u_net_pixel_to_patch.UNet(generator, path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"))
            model.train()
        elif args.model == "u_net_dropout":
            generator = ImageToPatchGenerator(os.path.join(properties["TRAIN_DIR_608"]),
                                              os.path.join(properties["TEST_DIR"]), 500, 200, True)

            print("[INFO] Path ", properties["OUTPUT_DIR"])
            model = u_net_pixel_to_patch.UNet(generator, path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"), type="dropout")
            model.train()

    elif args.predict:

        """
           Path to data to predict on,
           Path to the model to restore for predictions
        """
        data_path = args.data
        path_model_to_restore = os.path.join(get_latest_model(), "weights.h5")

        """Submission file"""
        submission_path_filename = get_submission_filename()

        print("[INFO] Loading the last checkpoint of the model ", args.model, " from: ", path_model_to_restore)

        if args.model == "cnn_lr_d":

            test_generator_class = PatchTestImageGenerator(path_to_images=os.path.join(data_path),
                                                           save_predictions_path=os.path.join(properties["OUTPUT_DIR"],
                                                                                              "predictions"))

            model_class = cnn_lr_d.CnnLrD(test_generator_class, path=path_model_to_restore)
            model = model_class.model

            print("[INFO] Model has been restored successfully")
            prediction_model = predict_on_tests.Prediction_model(test_generator_class=test_generator_class,
                                                                 restored_model=model)
            predictions = prediction_model.prediction_given_model()

            print("[INFO] Writing predictions to: ", submission_path_filename)
            prediction_model.save_predictions_to_csv(predictions=predictions, submission_file=submission_path_filename)

        elif args.model == "u_net":
            generator = ImageToPatchGenerator(os.path.join(properties["TRAIN_DIR_608"]),
                                              os.path.join(properties["TEST_DIR"]), 500, 200, True)

            print("[INFO] Path ", properties["OUTPUT_DIR"])
            model = u_net_pixel_to_patch.UNet(generator, path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"))
            model.predict(os.path.join(properties["TEST_DIR"]), submission_path_filename)

        elif args.model == "u_net_dropout":
            generator = ImageToPatchGenerator(os.path.join(properties["TRAIN_DIR_608"]),
                                              os.path.join(properties["TEST_DIR"]), 500, 200, True)

            print("[INFO] Path ", properties["OUTPUT_DIR"])
            model = u_net_pixel_to_patch.UNet(generator, path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"), type="dropout")
            model.predict(os.path.join(properties["TEST_DIR"]), submission_path_filename)

    elif args.visualize:
        print("[INFO] Visualizing predictions of the model: ", args.model)
        visualize(id_img=args.visualize, csv_file=get_latest_submission(), path_to_images=os.path.join(args.data),
                  patch_size=16)
