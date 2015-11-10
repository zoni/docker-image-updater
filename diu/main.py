from __future__ import print_function, absolute_import, unicode_literals, division

import argparse
import sys
import logging
import yaml

from diu.merge import merge
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

        if self.args.deprecated_file is not None:
            self.logger.warning(
                "--file is deprecated, please migrate to using positional"
                " arguments instead"
            )
            self._load_config(self.args.deprecated_file)
        else:
            self._load_config(*self.args.file)

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
            dest="deprecated_file",
            metavar="FILE",
            default=None,
            help="deprecated - this flag will be removed in the future",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="show debug messages"
        )
        parser.add_argument(
            "file",
            help="configuration file(s) to use",
            nargs="*",
            default=("/etc/docker-image-updater.yml",),
        )
        return parser

    def _load_config(self, *files):
        """
        Load and parse the given configuration file.

        :param files:
            One or more sets of configuration files to load.
        """
        final_config = {'config': {}, 'watch': {}}
        for f in files:
            try:
                data = yaml.safe_load(open(f))
            except (IOError, yaml.parser.ParserError) as e:
                print("Error loading {f}: {e!s}".format(f=f, e=e), file=sys.stderr)
                sys.exit(1)
            try:
                final_config = merge(final_config, data)
            except ValueError as e:
                print(
                    "You have an error in the configuration file {f}: {e!s}".format(f=f, e=e),
                    file=sys.stderr
                )
                sys.exit(1)

        self.config = final_config['config']
        for key, value in final_config['watch'].items():
            try:
                self._validate_watch_configuration(value)
            except ValueError as e:
                print(
                    "You have an error in the configuration file {f}: {e!s}".format(f=f, e=e),
                    file=sys.stderr
                )
                sys.exit(1)
            self.containerset.append(ContainerSet(
                name=key,
                images=value.get('images', []),
                commands=value.get('commands', []),
            ))

    def _validate_watch_configuration(self, watch):
        """
        Validate the structure of a 'watch' statement.
        """
        if not isinstance(watch, dict):
            raise ValueError("Key 'watch' should be a dictionary")
        if not isinstance(watch.get('images', []), list):
            raise ValueError("Key 'images' should be of type list")
        if not isinstance(watch.get('commands', []), list):
            raise ValueError("Key 'commands' should be of type list")

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
