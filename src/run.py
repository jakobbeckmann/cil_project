#!/usr/bin/env python3 -W ignore::DeprecationWarning

import argparse
import logging
import os
import sys
import warnings
import datetime
import time

from utils.commons import *

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)

# Remove tensorflow CPU instruction information.
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def _setup_argparser():
    """Sets up the argument parser and returns the arguments.

    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description="Control program to launch all actions related to"
                                                 " this project.")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-v", "--verbose",
                                 help="provide verbose output",
                                 action="store_true")
    verbosity_group.add_argument("-vv", "--very_verbose",
                                 help="provide even more verbose output",
                                 action="store_true")
    verbosity_group.add_argument("-q", "--quiet",
                                 help="provide next to no output to console",
                                 action="store_true")

    subparsers = parser.add_subparsers(dest="command", help="Test utilities")
    parser_c = subparsers.add_parser("check",
                                     help="Run unittest.main, accepts unittest options.")
    parser_c.add_argument("tests",
                          help="a list of any number of test modules, classes and test methods.",
                          nargs="*")
    parser_c.add_argument("-v", "--verbose",
                          help="Verbose Output",
                          action="store_true")
    parser_c.add_argument("-q", "--quiet",
                          help="Quiet Output",
                          action="store_true")
    parser_c.add_argument("--locals",
                          help="Show local variables in tracebacks",
                          action="store_true")
    parser_c.add_argument("-f", "--failfast",
                          help="Stop on first fail or error",
                          action="store_true")
    parser_c.add_argument("-c", "--catch",
                          help="Catch Ctrl-C and display results so far",
                          action="store_true")
    parser_c.add_argument("-b", "--buffer",
                          help="Buffer stdout and stderr during tests",
                          action="store_true")
    parser_c.add_argument("-p", "--pattern",
                          help="Pattern to match tests ('test*.py' default)")

    parser.add_argument("-m", "--model", action="store",
                        choices=["cnn_lr_d", "cnn_model", "full_cnn"],
                        default="cnn_lr_d",
                        type=str,
                        help="the CNN model to be used, defaults to cnn_lr_d")
    parser.add_argument("-t", "--train",
                        help="train the given CNN",
                        action="store_true")
    parser.add_argument("-tp", "--train_presume",
                        help="continue training the given CNN",
                        action="store_true")
    parser.add_argument("-p", "--predict",
                        help="predict on a test set given the CNN",
                        action="store_true")
    parser.add_argument("-d", "--data",
                        help="path to the data to use (prediction)",
                        action="store",
                        default=os.path.join(properties["TEST_DIR"], "data"),
                        type=str)
    parser.add_argument("-r", "--run",
                        help="run a trained version of a given CNN",
                        action="store_true")

    args, unknown = parser.parse_known_args()

    return args


def _setup_logger(args=None):
    """Set up the logger.

    Args:
        args (argparse.Namespace): the command line arguments from runnning the file.

    Returns:
        logging.Logger: A logger.
    """
    file_path = os.path.dirname(os.path.abspath(__file__))

    try:
        os.mkdir(properties["LOG_DIR"])
    except OSError:
        pass

    logger = logging.getLogger("cil_project")
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    logfile = logging.FileHandler(os.path.join(properties["LOG_DIR"], "run.log"), 'a')
    console_formatter = logging.Formatter("%(message)s")
    logfile_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console.setFormatter(console_formatter)
    logfile.setFormatter(logfile_formatter)

    logfile.setLevel(logging.WARNING)
    if args is None:
        console.setLevel(logging.INFO)
    elif args.very_verbose:
        console.setLevel(logging.DEBUG)
    elif args.verbose:
        console.setLevel(logging.INFO)
    elif not args.quiet:
        console.setLevel(logging.WARNING)
    else:
        console.setLevel(logging.ERROR)

    logger.addHandler(console)
    logger.addHandler(logfile)

    return logger


def get_latest_model():
    """Returns the latest directory of the model specified in the arguments.

    Returns:
        (path) a path to the directory.
    """
    if not os.path.exists(os.path.join(properties["SRC_DIR"], "../trained_models", args.model)):
        print("No trained model {} exists.".format(args.model))
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

    from keras.models import load_model

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
    elif args.train_presume:
        properties["OUTPUT_DIR"] = get_latest_model()
        properties["LOG_DIR"] = os.path.join(properties["OUTPUT_DIR"], "logs")
    else:
        properties["OUTPUT_DIR"] = os.path.normpath("..")

    properties["LOG_DIR"] = os.path.join(properties["OUTPUT_DIR"], "logs")

    _ = _setup_logger(args)
    logger = logging.getLogger("cil_project.src.run")

    from generators.FullTestImageGenerator import FullTestImageGenerator
    from generators.FullTrainImageGenerator import FullTrainImageGenerator
    from generators.PatchTrainImageGenerator import PatchTrainImageGenerator
    from generators.PatchTestImageGenerator import PatchTestImageGenerator
    from models import cnn_lr_d, cnn_model, full_cnn
    from models import predict_on_tests
    import keras
    import tests

    if args.command == "check":
        # Run code tests and exit
        logger.info("Running tests ...")
        logger.handlers[0].setLevel(logging.WARNING)
        sys.argv[1:] = sys.argv[2:]
        tests.run()
        sys.exit(0)

    if args.train:

        if args.model == "cnn_lr_d":
            train_generator = PatchTrainImageGenerator(os.path.join(properties["TRAIN_DIR"], "data"),
                                                       os.path.join(properties["TRAIN_DIR"], "verify"))
            validation_generator = PatchTrainImageGenerator(os.path.join(properties["VAL_DIR"], "data"),
                                                            os.path.join(properties["VAL_DIR"], "verify"))
            model = cnn_lr_d.CnnLrD(train_generator, validation_generator)
            try:
                model.train(not args.quiet)
            except KeyboardInterrupt:
                logger.warning("\nTraining interrupted")
            model.save(os.path.join(properties["OUTPUT_DIR"], "weights.h5"))

        elif args.model == "cnn_model":
            train_generator = PatchTrainImageGenerator(os.path.join(properties["TRAIN_DIR"], "data"),
                                                       os.path.join(properties["TRAIN_DIR"], "verify"))
            validation_generator = PatchTrainImageGenerator(os.path.join(properties["VAL_DIR"], "data"),
                                                            os.path.join(properties["VAL_DIR"], "verify"))
            model = cnn_model.CNN_keras(train_generator, validation_generator)
            try:
                model.train(not args.quiet)
            except KeyboardInterrupt:
                logger.warning("\nTraining interrupted")
            model.save(os.path.join(properties["OUTPUT_DIR"], "weights.h5"))

        elif args.model == "full_cnn":
            train_generator = FullTrainImageGenerator(os.path.join(properties["TRAIN_DIR"], "data"),
                                                      os.path.join(properties["TRAIN_DIR"], "verify"))
            validation_generator = FullTrainImageGenerator(os.path.join(properties["VAL_DIR"], "data"),
                                                           os.path.join(properties["VAL_DIR"], "verify"))
            model = full_cnn.FullCNN(train_generator, validation_generator)
            try:
                model.train(not args.quiet)
            except KeyboardInterrupt:
                logger.warning("\nTraining interrupted")
            model.save(os.path.join(properties["OUTPUT_DIR"], "weights.h5"))

    elif args.train_presume:
        train_generator = PatchTrainImageGenerator(os.path.join(properties["TRAIN_DIR"], "data"),
                                                   os.path.join(properties["TRAIN_DIR"], "verify"))
        validation_generator = PatchTrainImageGenerator(os.path.join(properties["VAL_DIR"], "data"),
                                                        os.path.join(properties["VAL_DIR"], "verify"))

        model = None
        if args.model == "cnn_lr_d":
            model = cnn_lr_d.CnnLrD(train_generator,
                                    validation_generator,
                                    path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"))

        elif args.model == "full_cnn":
            model = full_cnn.FullCNN(train_generator,
                                     validation_generator,
                                     path=os.path.join(properties["OUTPUT_DIR"], "weights.h5"))


        try:
            model.train(not args.quiet)
        except KeyboardInterrupt:
            logger.warning("\nTraining interrupted")
        model.save(os.path.join(properties["OUTPUT_DIR"], "weights.h5"))

    if args.predict:

        """
           Path to data to predict on,
           Path to the model to restore for predictions
        """
        data_path = args.data
        path_model_to_restore = os.path.join(get_latest_model(), "weights.h5")

        """Submission file"""
        submission_path_filename = get_submission_filename()

        print("Loading the last checkpoint of the model ", args.model, " from: ", path_model_to_restore)

        if args.model == "cnn_lr_d":

            test_generator_class = PatchTestImageGenerator(path_to_images=os.path.join(data_path),
                                                           save_predictions_path=os.path.join(properties["OUTPUT_DIR"],
                                                                                              "predictions"))

            model_class = cnn_lr_d.CnnLrD(test_generator_class, path=path_model_to_restore)
            model = model_class.model

            print("Model has been restored successfully")
            prediction_model = predict_on_tests.Prediction_model(test_generator_class=test_generator_class,
                                                                 restored_model=model)
            predictions = prediction_model.prediction_given_model()

            print("Writing predictions to: ", submission_path_filename)
            prediction_model.save_predictions_to_csv(predictions=predictions, submission_file=submission_path_filename)

        elif args.model == "cnn_model":
            # TODO error in the training -> to be fixed later on by the person who is responsible for the training part
            test_generator_class = PatchTestImageGenerator(path_to_images=os.path.join(data_path),
                                                           save_predictions_path=os.path.join(properties["OUTPUT_DIR"],
                                                                                              "predictions"),
                                                           four_dim=True)

            model_class = cnn_lr_d.CnnLrD(test_generator_class, path=path_model_to_restore)
            model = model_class.model

            print("Model has been restored successfully")
            prediction_model = predict_on_tests.Prediction_model(test_generator_class=test_generator_class,
                                                                 restored_model=model)
            predictions = prediction_model.prediction_given_model()

            print("Writing predictions to: ", submission_path_filename)
            prediction_model.save_predictions_to_csv(predictions=predictions, submission_file=submission_path_filename)

        elif args.model == "full_cnn":
            test_generator_class = FullTestImageGenerator(os.path.join(data_path))
            model = full_cnn.FullCNN(None, None)
            model.load(os.path.join(get_latest_model(), "weights.h5"))
            model.predict(test_generator_class)

    if args.run:
        # Test CNN model
        logger.warning("Requires training or predicting")
