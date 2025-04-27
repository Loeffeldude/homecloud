import os
from pathlib import Path
import typer
import hs_cli.commands

app = typer.Typer(
    name="hs-cli",
    help="hs-cli a cli for my personal homecloud",
    short_help="hs-cli a cli for my personal homecloud",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

app.add_typer(hs_cli.commands.app)

if __name__ == "__main__":
    import os

    os.chdir(str(Path(os.getcwd()).parent.absolute()))
    app()
