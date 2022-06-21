from os.path import dirname, abspath, join
import argparse

import yaml


def get_config(config_filename):
    """ Return config dict based on yaml filename.

    :param config_filename: string, filename in app directory - "donation_publisher_bot".
    :return: dict.
    """

    config_path = join(dirname(abspath(__file__)), config_filename)

    with open(config_path) as r:
        return yaml.safe_load(r)


def get_args():
    """ Return parsed command line args.

    :return: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Telegram donation publisher bot.",
        usage="main.py [--loop] [--sleep minutes]"
    )
    parser.add_argument("--loop", action="store_true", default=False,
                        help="If True then the bot runs in loop every sleep minutes.")
    parser.add_argument("--sleep", action="store", type=int, default=15,
                        help="Set sleep time between bot working. If not loop, then ignore.")
    parser.add_argument("--open_names", action="store_true", default=False,
                        help="If True then the bot will open donators' names.")
    return parser.parse_args()
