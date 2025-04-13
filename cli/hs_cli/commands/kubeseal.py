"""curl -OL "https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.29.0/kubeseal-0.29.0-linux-amd64.tar.gz"
tar -xvzf kubeseal-0.29.0-linux-amd64.tar.gz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal"""

import os
import pathlib
import subprocess
import tarfile
import typing
import typer
from rich.console import Console
from hs_cli.util import run_sudo_command_or_exit
import requests
import tempfile
import hs_cli.settings as settings

app = typer.Typer()
console = Console()
stderr_console = Console(stderr=True)


def verify_install():
    res = subprocess.run(
        ["kubeseal", "--version"],
        check=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    return res.returncode == 0


@app.command("install")
def install_kubeseak():
    if verify_install():
        stderr_console.print("kubeseal is already installed!")
        return

    response = requests.get(
        "https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.29.0/kubeseal-0.29.0-linux-amd64.tar.gz"
    )
    response.raise_for_status()

    with tempfile.TemporaryDirectory() as td:
        download_path = pathlib.Path(td) / "download.tar"
        with open(download_path) as tf:
            tf.write(response.content)
        tarfile.TarFile(download_path).extract(
            "kubeseal", pathlib.Path(td) / "kubeseal"
        )
        run_sudo_command_or_exit(
            ["sudo", "install", "-m", "755", "kubeseal", "/usr/local/bin/kubeseal"],
            "Installing kubeseal",
        )

    stderr_console.print("Verifiyng install...")

    verify_install()


@app.command("seal")
def seal(
    ctx: typer.Context,
    input_file_path: pathlib.Path,
    output_file_path: typing.Optional[pathlib.Path] = typer.Argument(
        default=None, help="the output file"
    ),
):
    cert_path = settings.K8S_DIR / "secrets_cert.pem"
    input_file_path = input_file_path.absolute()
    print(os.getcwd())
    if not cert_path.exists():
        stderr_console.print(f"[red]Cert at {str(cert_path)} does not exist[/red]")
        raise typer.Exit(1)

    if not output_file_path:
        output_file_path = pathlib.Path(str(input_file_path.parent))
        output_file_path = (
            output_file_path / f"{input_file_path.stem}-sealed{input_file_path.suffix}"
        )

    with input_file_path.open() as input_file:
        with output_file_path.open("w") as output_file:
            subprocess.run(
                [
                    "kubeseal",
                    "--format=yaml",
                    f"--cert={str(cert_path.absolute())}",
                ],
                stdin=input_file,
                stdout=output_file,
            )

    stderr_console.print(
        f"[green] Sealed {input_file_path} to {output_file_path} [/green]"
    )
