install-cli:
	./cli/scripts/install.sh

uninstall-cli:
	./cli/scripts/install.sh

install-pre-commit:
	pre-commit install

install: install-cli install-pre-commit
