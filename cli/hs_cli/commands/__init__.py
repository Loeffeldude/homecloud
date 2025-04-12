import typer
from .fluxcd import app as flux

app = typer.Typer()

app.add_typer(flux, name="flux")
