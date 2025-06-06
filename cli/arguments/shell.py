import argparse

from rasa.cli.arguments.default_arguments import (
    add_model_param,
    add_skip_validation_flag,
)
from rasa.cli.arguments.run import add_server_arguments


def set_shell_arguments(parser: argparse.ArgumentParser) -> None:
    add_model_param(parser)
    add_server_arguments(parser)
    add_skip_validation_flag(parser)


def set_shell_nlu_arguments(parser: argparse.ArgumentParser) -> None:
    add_model_param(parser)
