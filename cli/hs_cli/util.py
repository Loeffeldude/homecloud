from rich.console import Console
import typer
import subprocess

console = Console(stderr=True)


def run_sudo_command_or_exit(command, message, *args, **kwargs):
    if not run_sudo_command(command, message, *args, **kwargs):
        console.print("[red]This sudo operation needs to be run to continue.[/red]")
        raise typer.Exit(1)


def run_sudo_command(command, message, *args, **kwargs):
    """Run a command with sudo, with appropriate user feedback"""
    console.print(f"[bold blue]> {message}[/bold blue]")
    console.print(f"[dim]  Command: sudo {' '.join(command)}[/dim]")

    if not typer.confirm("Continue with sudo operation?", default=True):
        console.print("[yellow]Skipped sudo operation.[/yellow]")
        return False

    try:
        subprocess.run(["sudo"] + command, *args, check=True, **kwargs)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        return False
