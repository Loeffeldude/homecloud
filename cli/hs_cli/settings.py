from pathlib import Path


CLI_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = CLI_ROOT.parent

LOGS_DIR = PROJECT_ROOT / "logs"
DOCKER_DIR = PROJECT_ROOT / "docker"
K8S_DIR = PROJECT_ROOT / "k8s"
DATA_DIR = PROJECT_ROOT / "data"
