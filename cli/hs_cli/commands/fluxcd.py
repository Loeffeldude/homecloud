import dataclasses
import subprocess
import typer
from rich.console import Console
from hs_cli.util import run_sudo_command_or_exit
import os
import requests
import re
import hs_cli.settings as settings

app = typer.Typer()
console = Console()
stderr_console = Console(stderr=True)


@dataclasses.dataclass
class GitHubRepoInfo:
    username: str
    name: str
    remote_url: str
    remote_name: str
    main_branch_name: str

    @property
    def remote_url_https(self):
        if "https" in self.remote_url:
            return self.remote_url

        repo = self.remote_url.split("/")[-1]

        return f"https://github.com/{self.username}/{repo}"


def get_github_repo_name_and_user() -> GitHubRepoInfo:
    branches_res = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        check=True,
        stdout=subprocess.PIPE,
    )
    branches = branches_res.stdout.decode().split("\n")

    main_branch_name = None
    if "master" in branches:
        main_branch_name = "master"
    elif "main" in branches:
        main_branch_name = "main"

    main_branch_name = typer.prompt("Enter main branch name", default=main_branch_name)

    stderr_console.print("Main branch selected as", main_branch_name)

    remote_name_res = subprocess.run(
        ["git", "config", f"branch.{main_branch_name}.remote"],
        check=True,
        stdout=subprocess.PIPE,
    )
    remote_name = remote_name_res.stdout.decode()

    remote_url_res = subprocess.run(
        ["git", "remote", "get-url", remote_name.strip()],
        check=True,
        stdout=subprocess.PIPE,
    )

    remote_url = remote_url_res.stdout.decode().strip()

    if "github.com" not in remote_url:
        stderr_console.print("[red]This is not a GitHub repository.[/red]")
        raise typer.Exit(1)

    match = re.search(r"[:\/](\w+)\/(\w+).git", remote_url)

    if not match:
        stderr_console.print("Couldn't get user from git repo origin", remote_url)
        raise typer.Exit(1)

    return GitHubRepoInfo(
        username=match.group(1),
        main_branch_name=main_branch_name,
        name=match.group(2),
        remote_url=remote_url,
        remote_name=remote_name,
    )


def verify_flux_install():
    try:
        res = subprocess.run(
            ["flux", "--version"],
            check=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        return res.returncode == 0
    except:
        return False


def install_flux():
    if verify_flux_install():
        stderr_console.print("Flux is already installed!")
        return

    response = requests.get("https://fluxcd.io/install.sh")
    response.raise_for_status()

    run_sudo_command_or_exit(
        ["bash"],
        "Installing flux requires sudo. script from 'https://fluxcd.io/install.sh' will be executed",
        input=response.content,
    )

    stderr_console.print("Verifiyng install...")
    verify_flux_install()


@app.command("update-now")
def update_now():
    subprocess.run(
        [
            "flux",
            "reconcile",
            "source",
            "git",
            "flux-system",
        ],
        check=True,
    )

    subprocess.run(
        [
            "flux",
            "reconcile",
            "kustomization",
            "flux-system",
        ],
        check=True,
    )


@app.command("init")
def init_flux(dev: bool = False):
    """Initialize flux"""
    env = os.environ.copy()

    stderr_console.print("Installing Flux")

    install_flux()

    if dev:
        stderr_console.print("Installing flux without prod manifests...")
        subprocess.run(["flux", "install"])

        raise typer.Exit(0)
    repo_info = get_github_repo_name_and_user()
    username = typer.prompt("Enter GitHub username", default=repo_info.username)
    token = typer.prompt("Enter GitHub personal access token")

    subprocess.run(
        [
            "flux",
            "bootstrap",
            "github",
            "--token-auth",
            f"--owner={username}",
            f"--repository={repo_info.name}",
            f"--branch={repo_info.main_branch_name}",
            "--path=k8s",
            "--personal",
        ],
        env={
            **env,
            "GITHUB_TOKEN": token,
        },
        check=True,
    )

    git_resource_res = subprocess.run(
        [
            "flux",
            "create",
            "source",
            "git",
            "podinfo",
            f"--url={repo_info.remote_url_https}",
            f"--branch={repo_info.main_branch_name}",
            "--interval=1m",
            "--export",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )

    resource_path = settings.PROJECT_ROOT / "k8s" / "base" / "git-repo.yaml"

    if resource_path.exists():
        subprocess.run(
            ["diff", str(resource_path.absolute()), "-"], stdin=git_resource_res.stdout
        )
        typer.confirm(
            f"[bold blue] {str(resource_path)} already exists! Overwrite?[/bold blue]"
        )

    stderr_console.print("Written file ", str(resource_path))
    resource_path.write_bytes(git_resource_res.stdout)
