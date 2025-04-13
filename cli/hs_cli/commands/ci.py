import pathlib
import subprocess
import tarfile
import typer
from rich.console import Console
from hs_cli.util import run_sudo_command_or_exit
import requests
import tempfile

["kubectl", "apply", "-f", "deployment.yaml", "--dry-run=client"]


app = typer.Typer()
console = Console()
stderr_console = Console(stderr=True)
