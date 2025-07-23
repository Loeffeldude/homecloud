import typer
from .fluxcd import app as flux
from .kubeseal import app as kubeseal
from .config import app as config

app = typer.Typer()

app.add_typer(flux, name="flux")
app.add_typer(kubeseal, name="kubeseal")
app.add_typer(config, name="config")
