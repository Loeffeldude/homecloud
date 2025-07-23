import pathlib
import subprocess
import typing
import typer
from rich.console import Console
from rich.table import Table
import yaml
import yaml.parser
import hs_cli.settings as settings
import os
import sys
import tempfile

app = typer.Typer()
console = Console()
stderr_console = Console(stderr=True)


def get_all_yaml_files() -> typing.List[pathlib.Path]:
    yaml_files = []
    for dir_path, _, files in os.walk(settings.K8S_DIR):
        dir_path = pathlib.Path(dir_path)
        for file_path_str in files:
            file_path = dir_path / pathlib.Path(file_path_str)
            if file_path.suffix in [".yaml", ".yml"]:
                yaml_files.append(file_path)
    return yaml_files


def validate_yaml_syntax(file_path: pathlib.Path) -> typing.Tuple[bool, str]:
    try:
        content = file_path.read_text()
        list(yaml.safe_load_all(content))
        return True, ""
    except yaml.parser.ParserError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def validate_kubernetes_manifest(file_path: pathlib.Path) -> typing.Tuple[bool, str]:
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            temp_file.write(file_path.read_text())
            temp_file_path = temp_file.name

        result = subprocess.run(
            [
                "kubectl",
                "apply",
                "--dry-run=client",
                "--validate=true",
                "-f",
                temp_file_path,
            ],
            capture_output=True,
            text=True,
        )

        os.unlink(temp_file_path)

        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr.strip()

    except FileNotFoundError:
        return False, "kubectl not found in PATH"
    except Exception as e:
        return False, str(e)


@app.command("validate")
def validate(
    strict: bool = typer.Option(
        False, "--strict", help="Validate against Kubernetes API"
    )
):
    yaml_files = get_all_yaml_files()

    if not yaml_files:
        stderr_console.print("[yellow]No YAML files found in k8s directory[/yellow]")
        return

    table = Table(title="Validation Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Error", style="red")

    total_files = len(yaml_files)
    valid_files = 0

    for file_path in yaml_files:
        relative_path = file_path.relative_to(settings.PROJECT_ROOT)

        yaml_valid, yaml_error = validate_yaml_syntax(file_path)

        if not yaml_valid:
            table.add_row(str(relative_path), "❌ Invalid YAML", yaml_error)
            continue

        if strict:
            k8s_valid, k8s_error = validate_kubernetes_manifest(file_path)
            if not k8s_valid:
                table.add_row(str(relative_path), "❌ Invalid K8s", k8s_error)
                continue

        table.add_row(str(relative_path), "✅ Valid", "")
        valid_files += 1

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {valid_files}/{total_files} files valid")

    if valid_files != total_files:
        raise typer.Exit(1)


@app.command("diff")
def diff(
    source: str = typer.Argument(
        help="Source environment (e.g., 'staging', 'prod', or path)"
    ),
    target: str = typer.Argument(
        help="Target environment (e.g., 'staging', 'prod', or path)"
    ),
    context: int = typer.Option(3, "--context", "-c", help="Number of context lines"),
):
    def resolve_path(env_or_path: str) -> pathlib.Path:
        if env_or_path in ["staging", "prod", "dev"]:
            env_path = settings.K8S_DIR / env_or_path
            if env_path.exists():
                return env_path
            else:
                stderr_console.print(
                    f"[red]Environment '{env_or_path}' not found at {env_path}[/red]"
                )
                raise typer.Exit(1)
        else:
            path = pathlib.Path(env_or_path)
            if path.exists():
                return path.resolve()
            else:
                stderr_console.print(f"[red]Path '{env_or_path}' does not exist[/red]")
                raise typer.Exit(1)

    source_path = resolve_path(source)
    target_path = resolve_path(target)

    if source_path == target_path:
        console.print("[green]No differences found (same path)[/green]")
        return

    try:
        result = subprocess.run(
            [
                "diff",
                "-r",
                f"--context={context}",
                "--exclude=*.secretraw.*",
                str(source_path),
                str(target_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]No differences found[/green]")
        elif result.returncode == 1:
            console.print(f"[bold]Differences between {source} and {target}:[/bold]\n")
            console.print(result.stdout)
        else:
            stderr_console.print(f"[red]Error running diff: {result.stderr}[/red]")
            raise typer.Exit(1)

    except FileNotFoundError:
        stderr_console.print("[red]diff command not found in PATH[/red]")
        raise typer.Exit(1)
