"""curl -OL "https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.29.0/kubeseal-0.29.0-linux-amd64.tar.gz"
tar -xvzf kubeseal-0.29.0-linux-amd64.tar.gz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal"""

import pathlib
import re
import subprocess
import tarfile
import typing
import typer
from rich.console import Console
import yaml
import yaml.parser
from hs_cli.util import run_sudo_command_or_exit
import requests
import tempfile
import hs_cli.settings as settings
import os

app = typer.Typer()
console = Console()
stderr_console = Console(stderr=True)
CERT_PATH = settings.K8S_DIR / "secrets_cert.pem"


def verify_install():
    res = subprocess.run(
        ["kubeseal", "--version"],
        check=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )

    return res.returncode == 0


def seal_file(file_path: pathlib.Path, cert_path: pathlib.Path = CERT_PATH) -> str:
    if not cert_path.exists():
        stderr_console.print(f"[red]Cert at {str(cert_path)} does not exist[/red]")
        raise typer.Exit(1)

    with file_path.open() as input_file:
        result = subprocess.run(
            [
                "kubeseal",
                "--format=yaml",
                f"--cert={str(cert_path.absolute())}",
            ],
            check=True,
            stdin=input_file,
            stdout=subprocess.PIPE,
        )

    return result.stdout.decode()


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
    CERT_PATH = settings.K8S_DIR / "secrets_cert.pem"
    input_file_path = input_file_path.absolute()

    if not output_file_path:
        output_file_path = pathlib.Path(str(input_file_path.parent))
        output_file_path = (
            output_file_path / f"{input_file_path.stem}-sealed{input_file_path.suffix}"
        )

    if output_file_path.exists():
        should_overwrite = typer.confirm(
            f"[red]file at {str(output_file_path.absolute())} exists. Do you want to override it?"
        )

        if not should_overwrite:
            raise typer.Exit(1)

    with output_file_path.open("w") as output_file:
        seal_file(output_file)

    stderr_console.print(
        f"[green] Sealed {input_file_path} to {output_file_path} [/green]"
    )


@app.command("sealall")
def sealall():
    for dir, _, files in os.walk(settings.K8S_DIR):
        dir_path = pathlib.Path(dir)
        for file_path_str in files:
            file_path = dir_path / pathlib.Path(file_path_str)
            is_yaml = file_path.suffix == ".yaml" or file_path.suffix == ".yml"

            if not is_yaml:
                continue

            kinds = set()
            UNSET = object()
            try:
                for document in yaml.safe_load_all(file_path.read_text()):
                    kind = dict(document).get("kind", UNSET)

                    if kind is UNSET:
                        continue

                    kinds.add(kind)

                has_secret = "Secret" in kinds
                is_mixed_type = len(kinds) > 1

                name_match = re.match(r"(.*)\.secretraw.ya?ml", file_path.name)
                is_correctly_named = bool(name_match)

                if not has_secret:
                    continue

                if is_mixed_type:
                    kinds_str = ", ".join(kinds)
                    stderr_console.print(
                        f"[yellow]{file_path} has kinds {kinds_str}. Please only use kind Secret in a sealed document! [/yellow]"
                    )
                    stderr_console.print(
                        f"[yellow]{file_path} Ignored see above[/yellow]"
                    )
                    continue

                if not is_correctly_named:
                    stderr_console.print(
                        f"[yellow]{file_path} contains only secrets but does not match git ignore pattern for secrets! please name your file *.secretraw.yaml/*.secretraw.yml or it will be commited to git! [/yellow]"
                    )
                    stderr_console.print(
                        f"[yellow]{file_path} Ignored see above[/yellow]"
                    )
                    continue

                sealed_file = seal_file(file_path)
                sealed_file_path = dir_path / f"{name_match.group(1)}{file_path.suffix}"

                sealed_file_path.write_text(sealed_file)
                stderr_console.print(f"[green]{sealed_file_path} written![/green]")
            except yaml.parser.ParserError:
                stderr_console.print(f"[red] failed parsing {file_path}[/red]")
