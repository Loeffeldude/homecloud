import typer
from .fluxcd import app as flux
from .kubeseal import app as kubeseal
from .config import app as config
from .ci import app as ci

app = typer.Typer(no_args_is_help=True)

app.add_typer(flux, name="flux")
app.add_typer(kubeseal, name="kubeseal")
app.add_typer(config, name="config")
app.add_typer(flux, name="flux")
app.add_typer(ci, name="ci")
