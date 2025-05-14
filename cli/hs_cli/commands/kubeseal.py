"""curl -OL "https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.29.0/kubeseal-0.29.0-linux-amd64.tar.gz"
tar -xvzf kubeseal-0.29.0-linux-amd64.tar.gz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal"""

import pathlib
import re
import subprocess
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
    try:
        res = subprocess.run(
            ["kubeseal", "--version"],
            check=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        return res.returncode == 0
    except FileNotFoundError:
        return False


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
        download_path = pathlib.Path(td) / "download.tar.gz"
        with open(download_path, "wb") as tf:
            tf.write(response.content)

        assert download_path.exists()

        subprocess.run(["tar", "-xf", download_path, "-C", td, "kubeseal"], check=True)

        run_sudo_command_or_exit(
            [
                "sudo",
                "install",
                "-m",
                "755",
                str(pathlib.Path(td) / "kubeseal"),
                "/usr/local/bin/kubeseal",
            ],
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
    input_file_path = input_file_path.absolute()

    if not output_file_path:
        name_match = re.match(r"(.*)\.secretraw.ya?ml", input_file_path.name)

        if name_match:
            out_name = f"{name_match.group(1)}{input_file_path.suffix}"
        else:
            out_name = f"{input_file_path.stem}-sealed{input_file_path.suffix}"

        output_file_path = pathlib.Path(str(input_file_path.parent))
        output_file_path = output_file_path / out_name

    if output_file_path.exists():
        should_overwrite = typer.confirm(
            f"[red]file at {str(output_file_path.absolute())} exists. Do you want to override it?"
        )

        if not should_overwrite:
            raise typer.Exit(1)

    with output_file_path.open("w") as output_file:
        output_file.write(seal_file(input_file_path))

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


@app.command("unsealall")
def unsealall(
    private_key_path: typing.Optional[pathlib.Path] = typer.Argument(
        None, help="Path to private key file used for unsealing"
    ),
    private_key: typing.Optional[str] = typer.Option(
        None, "--key", help="Private key content used for unsealing"
    ),
):
    """
    Decrypt all sealed secret files in the Kubernetes directory using a private key.
    Intended for disaster recovery scenarios.
    """
    if not private_key_path and not private_key:
        stderr_console.print(
            "[red]Error: Either private key path or private key content must be provided[/red]"
        )
        raise typer.Exit(1)

    # Create temporary file if private key content is provided
    temp_key_file = None
    key_path_to_use = private_key_path

    if private_key and not private_key_path:
        temp_key_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        temp_key_file.write(private_key)
        temp_key_file.close()
        key_path_to_use = pathlib.Path(temp_key_file.name)

    try:
        if not key_path_to_use.exists():
            stderr_console.print(
                f"[red]Private key file {key_path_to_use} does not exist[/red]"
            )
            raise typer.Exit(1)

        unsealed_count = 0

        for dir_path, _, files in os.walk(settings.K8S_DIR):
            dir_path = pathlib.Path(dir_path)
            for file_path_str in files:
                file_path = dir_path / pathlib.Path(file_path_str)
                is_yaml = file_path.suffix == ".yaml" or file_path.suffix == ".yml"

                if not is_yaml:
                    continue

                # Skip files that are already marked as raw secrets
                if ".secretraw." in file_path.name:
                    continue

                try:
                    # Check if file contains SealedSecret kind
                    contains_sealed_secret = False
                    for document in yaml.safe_load_all(file_path.read_text()):
                        if document and document.get("kind") == "SealedSecret":
                            contains_sealed_secret = True
                            break

                    if not contains_sealed_secret:
                        continue

                    # Determine output file name
                    output_name = f"{file_path.stem}.secretraw{file_path.suffix}"
                    output_path = file_path.parent / output_name

                    # Unseal the secret
                    with file_path.open("r") as input_file:
                        result = subprocess.run(
                            [
                                "kubeseal",
                                "-o",
                                "yaml",
                                "--recovery-unseal",
                                f"--recovery-private-key={str(key_path_to_use)}",
                            ],
                            check=True,
                            stdin=input_file,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )

                    # Write unsealed content to output file
                    output_path.write_text(result.stdout.decode())
                    unsealed_count += 1
                    stderr_console.print(
                        f"[green]Unsealed {file_path} to {output_path}[/green]"
                    )

                except yaml.parser.ParserError:
                    stderr_console.print(
                        f"[red]Failed to parse {file_path} as YAML[/red]"
                    )
                except subprocess.CalledProcessError as e:
                    stderr_console.print(
                        f"[red]Failed to unseal {file_path}: {e.stderr.decode()}[/red]"
                    )

        if unsealed_count == 0:
            stderr_console.print("[yellow]No sealed secrets found to unseal[/yellow]")
        else:
            stderr_console.print(
                f"[green]Successfully unsealed {unsealed_count} secret files[/green]"
            )

    finally:
        # Clean up temporary file if created
        if temp_key_file:
            os.unlink(temp_key_file.name)
