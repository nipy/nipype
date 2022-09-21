#!python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import click

from .instance import list_interfaces
from .utils import (
    CONTEXT_SETTINGS,
    UNKNOWN_OPTIONS,
    ExistingDirPath,
    ExistingFilePath,
    UnexistingFilePath,
    RegularExpression,
    PythonModule,
    check_not_none,
)

from .. import __version__


# declare the CLI group
@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument("logdir", type=ExistingDirPath, callback=check_not_none)
@click.option(
    "-r",
    "--regex",
    type=RegularExpression(),
    callback=check_not_none,
    help="Regular expression to be searched in each traceback.",
)
def search(logdir, regex):
    """Search for tracebacks content.

    Search for traceback inside a folder of nipype crash log files that match
    a given regular expression.

    Examples:\n
    nipypecli search nipype/wd/log -r '.*subject123.*'
    """
    from .crash_files import iter_tracebacks

    for file, trace in iter_tracebacks(logdir):
        if regex.search(trace):
            click.echo("-" * len(file))
            click.echo(file)
            click.echo("-" * len(file))
            click.echo(trace)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument("crashfile", type=ExistingFilePath, callback=check_not_none)
@click.option(
    "-r", "--rerun", is_flag=True, flag_value=True, help="Rerun crashed node."
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    flag_value=True,
    help="Enable Python debugger when re-executing.",
)
@click.option(
    "-i",
    "--ipydebug",
    is_flag=True,
    flag_value=True,
    help="Enable IPython debugger when re-executing.",
)
@click.option(
    "-w", "--dir", type=ExistingDirPath, help="Directory where to run the node in."
)
def crash(crashfile, rerun, debug, ipydebug, dir):
    """Display Nipype crash files.

    For certain crash files, one can rerun a failed node in a temp directory.

    Examples:\n
    nipypecli crash crashfile.pklz\n
    nipypecli crash crashfile.pklz -r -i\n
    """
    from .crash_files import display_crash_file

    debug = "ipython" if ipydebug else debug
    if debug == "ipython":
        import sys
        from IPython.core import ultratb

        sys.excepthook = ultratb.FormattedTB(
            mode="Verbose", color_scheme="Linux", call_pdb=1
        )
    display_crash_file(crashfile, rerun, debug, dir)


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.argument("pklz_file", type=ExistingFilePath, callback=check_not_none)
def show(pklz_file):
    """Print the content of Nipype node .pklz file.

    Examples:\n
    nipypecli show node.pklz
    """
    from pprint import pprint
    from ..utils.filemanip import loadpkl

    pkl_data = loadpkl(pklz_file)
    pprint(pkl_data)


@cli.command(context_settings=UNKNOWN_OPTIONS)
@click.argument("module", type=PythonModule(), required=False, callback=check_not_none)
@click.argument("interface", type=str, required=False)
@click.option(
    "--list",
    is_flag=True,
    flag_value=True,
    help="List the available Interfaces inside the given module.",
)
@click.option(
    "-h", "--help", is_flag=True, flag_value=True, help="Show help message and exit."
)
@click.pass_context
def run(ctx, module, interface, list, help):
    """Run a Nipype Interface.

    Examples:\n
    nipypecli run nipype.interfaces.nipy --list\n
    nipypecli run nipype.interfaces.nipy ComputeMask --help
    """
    import argparse
    from .utils import add_args_options
    from ..utils.nipype_cmd import run_instance

    # print run command help if no arguments are given
    module_given = bool(module)
    if not module_given:
        click.echo(ctx.command.get_help(ctx))

    # print the list of available interfaces for the given module
    elif (module_given and list) or (module_given and not interface):
        iface_names = list_interfaces(module)
        click.echo("Available Interfaces:")
        for if_name in iface_names:
            click.echo("    {}".format(if_name))

    # check the interface
    elif module_given and interface:
        # create the argument parser
        description = "Run {}".format(interface)
        prog = " ".join([ctx.command_path, module.__name__, interface] + ctx.args)
        iface_parser = argparse.ArgumentParser(description=description, prog=prog)

        # instantiate the interface
        node = getattr(module, interface)()
        iface_parser = add_args_options(iface_parser, node)

        if not ctx.args:
            # print the interface help
            try:
                iface_parser.print_help()
            except:
                print(
                    "An error occurred when trying to print the full"
                    "command help, printing usage."
                )
            finally:
                iface_parser.print_usage()
        else:
            # run the interface
            args = iface_parser.parse_args(args=ctx.args)
            run_instance(node, args)


@cli.command(context_settings=CONTEXT_SETTINGS)
def version():
    """Print current version of Nipype."""
    click.echo(__version__)


@cli.group()
def convert():
    """Export nipype interfaces to other formats."""
    pass


@convert.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-i",
    "--interface",
    type=str,
    required=True,
    help="Name of the Nipype interface to export.",
)
@click.option(
    "-m",
    "--module",
    type=PythonModule(),
    required=True,
    callback=check_not_none,
    help="Module where the interface is defined.",
)
@click.option(
    "-o",
    "--output",
    type=UnexistingFilePath,
    required=True,
    callback=check_not_none,
    help="JSON file name where the Boutiques descriptor will be " "written.",
)
@click.option(
    "-c",
    "--container-image",
    required=True,
    type=str,
    help="Name of the container image where the tool is installed.",
)
@click.option(
    "-p",
    "--container-type",
    required=True,
    type=str,
    help="Type of container image (Docker or Singularity).",
)
@click.option(
    "-x",
    "--container-index",
    type=str,
    help="Optional index where the image is available (e.g. "
    "http://index.docker.io).",
)
@click.option(
    "-g",
    "--ignore-inputs",
    type=str,
    multiple=True,
    help="List of interface inputs to not include in the descriptor.",
)
@click.option(
    "-v", "--verbose", is_flag=True, flag_value=True, help="Print information messages."
)
@click.option(
    "-a", "--author", type=str, help="Author of the tool (required for publishing)."
)
@click.option(
    "-t",
    "--tags",
    type=str,
    help="JSON string containing tags to include in the descriptor,"
    'e.g. "{"key1": "value1"}"',
)
def boutiques(
    module,
    interface,
    container_image,
    container_type,
    output,
    container_index,
    verbose,
    author,
    ignore_inputs,
    tags,
):
    """Nipype to Boutiques exporter.

    See Boutiques specification at https://github.com/boutiques/schema.
    """
    from nipype.utils.nipype2boutiques import generate_boutiques_descriptor

    # Generates JSON string and saves it to file
    generate_boutiques_descriptor(
        module,
        interface,
        container_image,
        container_type,
        container_index,
        verbose,
        True,
        output,
        author,
        ignore_inputs,
        tags,
    )
