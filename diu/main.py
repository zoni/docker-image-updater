import argparse
import sys
import logging
import yaml

from diu.updater import ContainerSet, Updater
from docker import Client as DockerClient

try:
    from colorlog import ColoredFormatter
except ImportError:
    ColoredFormatter = None


class Application(object):
    """
    The docker image updater application.
    """

    def __init__(self, args=None):
        """
        :param args:
            Program arguments. If not supplied, will use sys.argv
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parser = self._create_parser()
        self.args = self.parser.parse_args(args=args)
        if self.args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        self.containerset = []
        self._load_config(self.args.file)

        d = DockerClient(**self.config.get('docker', {}))
        self.updater = Updater(d, self.containerset)

    def _create_parser(self):
        """
        Create the argparse argument parser.

        :returns:
            An instance of `argparse.ArgumentParser()`
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-f", "--file",
            default="config.yml",
            help="the config file to use"
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="show debug messages"
        )
        return parser

    def _load_config(self, file):
        """
        Load and parse the given configuration file.

        :param file:
            Path of the file to parse
        """
        data = yaml.safe_load(open(file))
        self.config = data.get('config', {})
        for key, value in data['watch'].items():
            self.containerset.append(ContainerSet(name=key, **value))

    def run(self):
        """
        Run the application.
        """
        self.updater.do_updates()
        if self.updater.error_count > 0:
            sys.exit(1)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    if sys.stdout.isatty() and ColoredFormatter is not None:
        formatter = ColoredFormatter(
            "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s "
            "%(cyan)s%(name)-10s%(reset)s %(white)s%(message)s%(reset)s",
            datefmt="%H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG': 'blue',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)-10s %(message)s",
            datefmt="%H:%M:%S",
        )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def main():
    setup_logger()
    Application().run()
