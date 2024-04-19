# CLI support
from jztools.validation import checked_get_single
from importlib import import_module
import sys
import argparse
import hydra
from typing import Callable, Optional, List
from pathlib import Path
from xerializer import Serializer
from omegaconf import DictConfig, OmegaConf
from frozendict import frozendict
from xerializer._argparse import Argument

ARGPARSE_ARGUMENT_MODULES = Argument(
    "--modules",
    help=(
        "A list of comma-separated modules (e.g., `--modules='my.module1, my.module2'`, "
        "whitespace optional) to load. This can be used e.g., to register "
        "xerializable types."
    ),
    nargs=1,
)


def import_parser_modules(modules):
    if modules:
        [
            import_module(_module)
            for _module in map(str.strip, checked_get_single(modules).split(","))
            if _module
        ]


def _deserialize_hydra(fxn, expected_type=None, serializer=None, **fxn_kwargs):
    """
    Decorator that maps serializable'd objects to objects in the :class:`omegaconf.DictConfig` input, and calls the child with keyword args derived from the cfg object.
    """
    serializer = serializer or Serializer()

    def out_fxn(cfg: DictConfig):
        OmegaConf.resolve(cfg)
        obj = serializer.from_serializable(OmegaConf.to_container(cfg))
        if expected_type and not isinstance(obj, expected_type):
            raise TypeError(
                f"Expected {expected_type} but received type-{type(obj)} object {obj}."
            )
        fxn(obj, **fxn_kwargs)

    return out_fxn


def worker(deserialized_object):
    deserialized_object.train()


def hydra_cli(
    worker: Callable,
    expected_type: Optional[type] = None,
    serializer: Optional[Serializer] = None,
    cli_args: List[Argument] = None,
    excluded_cli_args: List[str] = None,
    override_hydra_run_dir: bool = True,
    override_hydra_logging: bool = True,
):
    """

    :param worker: Callable to execute on the deserialized object. It will take as parameters the deserialized object received from config file, and all ``cli_args`` as keyword arguments.
    :param expected_type: The expected ``type`` of the serialized object. If provided, receiving an object of a different type will raise an error.
    :param serializer: The serializer to use when deserializing the provided objects. By default, :class:`~xerializer.serializer.Serializer()` will be used with no arguments.
    :param cli_args: List of extra CLI arguments to accept. These arguments will be passed to the worker function as keyword arguments.
    :param excluded_cli_args: Name of args in ``cli_args`` that will not be passed to the worker but will be returned.
    :param override_hydra_run_dir: If ``True`` (the default), the working directory will be set to the output directory.
    :param override_hydra_logging: If ``True`` (the default), disables Hydra's automatic logging configuration.

    .. rubric:: CLI Arguments

    This function creates a CLI that takes the following arguments:

    #. A root configuration file in `Hydra <https://hydra.cc/>`_ format. This file might point internally to other configuration files. See, e.g., `Grouping config files <https://hydra.cc/docs/tutorials/basic/your_first_app/config_groups>`_ in the Hydra documentation.
    #. An output directory that will become the working directory.
    #. Optional arguments in Hydra syntax that override or extend values in the configuration files.

    .. rubric:: Comparison to Hydra CLI

    The CLI executes a specified worker function that takes as input the object loaded form the hydra configuration file, similarly to what using the ``@hydra.main()`` decorator does. The produced CLI will have the following two differences relative to that approach:

    #. It will use the specified output directory as the working directory.
    #. It will deserialize the object loaded from the configuration file using :class:`~xerializer.serializer.Serializer` before passing it to the worker function.


    .. rubric:: Example

    The following example shows how to build a CLI for a worker function ``add()``:

    .. code-block::

      from xerializer import serializable

      # This class can be defined in a separate file.
      @serializable()
      class MyClass:
        def __init__(self, a:int, b:int):
          self.a = a
          self.b = b

      def add(obj: MyClass):
        return obj.a + obj.b

      if __name__=='__main__':
         # Argument ``expected_type`` is optional.
         hydra_cli(add, expected_type=MyClass)[0]()

    You can then invoke that file directly from the command line (requires the ``#!/usr/bin/env python`` shebang as the first line of your file)

    .. code-block:: bash

      >> chmod 755 ./my_train_manager.py # Sets executable permissions, needed only once.
      # Top-line '#!/usr/bin/env python' shebang required.
      >> ./my_train_manager.py ./config/train.yaml output_dir/

    or as an argument to the ``python`` command,

    .. code-block:: bash

      >> python ./my_train_manager.py ./config/train.yaml output_dir/

    where we assume that ``'./config/train.yaml'`` contains an xerialized representation of a ``MyClass`` object.
    """

    # Parse meta arguments config and output_dir
    parser = argparse.ArgumentParser(description="Train a model.")
    parser.add_argument(
        "config", type=Path, help="Path to hydra *.yaml configuration file."
    )
    parser.add_argument("output_dir", type=Path, help="Output directory root.")

    # Pre-process extra args.
    cli_args = cli_args or []
    excluded_cli_args = excluded_cli_args or []
    excluded_cli_args = [x.replace("-", "_") for x in excluded_cli_args]

    # Add extra arguments.
    worker_kwarg_names = [_arg.bind(parser).dest for _arg in cli_args]

    # Comma-separated list of extra modules to load
    ARGPARSE_ARGUMENT_MODULES.bind(parser)

    # Extra hydra parameters.
    parser.add_argument(
        "hydra_overrides",
        nargs="*",
        help="Configuration file overrides in Hydra syntax.",
    )

    # Split argparse and hydra arguments
    parsed_args = parser.parse_args()

    # Import all extra modules
    import_parser_modules(parsed_args.modules)

    # Build and execute hydra.main()
    config_path = parsed_args.config.absolute()
    config_path_root = str(config_path.parent)
    config_name = str(config_path.stem)
    assert (
        config_path.suffix == ".yaml"
    ), f"Expected a *.yaml config path, but received a *{config_path.suffix}."

    # Prepare args for hydra.
    orig_args = list(sys.argv)

    arg0 = sys.argv[0]
    sys.argv.clear()
    esc_eq = r"\="
    sys.argv.extend(
        [arg0]
        + (
            [
                f"hydra.run.dir={str(parsed_args.output_dir.absolute()).replace('=', esc_eq)}"
            ]
            if override_hydra_run_dir
            else []
        )
        + (
            ["hydra/job_logging=none", "hydra/hydra_logging=none"]
            if override_hydra_logging
            else []
        )
        + parsed_args.hydra_overrides
    )

    wrapped_call = _deserialize_hydra(
        worker,
        expected_type=expected_type,
        serializer=serializer,
        **{
            _name: getattr(parsed_args, _name)
            for _name in worker_kwarg_names
            if _name not in excluded_cli_args
        },
    )

    # Required for config-path trick above to work.
    # Otherwise, hydra assumes the patch is relative to the
    # xerializer package
    wrapped_call.__module__ = None

    return (
        hydra.main(
            config_path=config_path_root,  # Relative to hydra.searchpath, set above.
            config_name=config_name,
        )(wrapped_call),
        parsed_args,
        orig_args,
    )
