import os
from pathlib import Path
import sys

CLI_ROOT = Path(os.path.abspath(sys.argv[0])).parent
PROJECT_ROOT = CLI_ROOT.parent

LOGS_DIR = PROJECT_ROOT / "logs"
DOCKER_DIR = PROJECT_ROOT / "docker"
K8S_DIR = PROJECT_ROOT / "k8s"
DATA_DIR = PROJECT_ROOT / "data"
