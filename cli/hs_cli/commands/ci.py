import pathlib
import itertools
import subprocess
import tarfile
import typer
from rich.console import Console
from hs_cli import settings
from hs_cli.util import run_sudo_command_or_exit
import requests
import tempfile
import glob
import yaml

app = typer.Typer()
console = Console()
stderr_console = Console(stderr=True)


def is_file_tracked(filepath):
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


@app.command("check_for_secrets")
def check_for_secrets():
    found = False
    for file_path in itertools.chain(
        settings.K8S_DIR.glob("**/*.yaml"), settings.K8S_DIR.glob("**/*.yml")
    ):
        if not is_file_tracked(file_path):
            continue

        for document in yaml.safe_load_all(file_path.read_text()):
            if not isinstance(document, dict):
                continue

            resource_type = document.get("kind", None)

            if resource_type != "Secret":
                continue

            is_allowed = document.get("x-allow-secret", False)

            if is_allowed:
                stderr_console.print(
                    f"[yellow]WARNING: {str(file_path.absolute())} is explicitly allowed[/yellow]"
                )
                continue

            found = True
            console.print(str(file_path.absolute()))
            break

    if found:
        stderr_console.print("[red]files are tracked by git and contain secrets![/red]")
        stderr_console.print(
            "Either allow the files by adding a `x-allow-secret: true` in the top level of the document or untrack the file with git"
        )
        raise typer.Exit(1)

    stderr_console.print("[green]No secrets found! [/green]")
