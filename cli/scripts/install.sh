#!/usr/bin/env bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Version
VERSION="1.0.0"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLI_DIR="$SCRIPT_DIR/../"
INSTALL_DIR="$HOME/.local/bin"
MIN_PYTHON_VERSION="3.8"

# Print banner
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════╗"
echo "║          HomeCloud CLI Installer              ║"
echo "║           Version: ${VERSION}                     ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if ! command_exists python3; then
        echo -e "${RED}Error: Python 3 is not installed. Please install Python ${MIN_PYTHON_VERSION} or newer.${NC}"
        exit 1
    fi
    
    # Get Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    
    # Compare versions
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (${MIN_PYTHON_VERSION//./, }) else 1)"; then
        echo -e "${RED}Error: Python ${MIN_PYTHON_VERSION} or newer is required, but Python ${python_version} is installed.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python ${python_version} detected${NC}"
}

# Function to install Poetry
install_poetry() {
    echo -e "${BLUE}Installing Poetry...${NC}"
    
    # Set POETRY_HOME to user's home directory
    export POETRY_HOME="$HOME/.poetry"
    
    # Install Poetry with the official installer
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for the current session
    export PATH="$HOME/.poetry/bin:$PATH"
    
    # Check if installation was successful
    if ! command_exists poetry; then
        echo -e "${RED}Failed to install Poetry. Please install it manually: https://python-poetry.org/docs/#installation${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Poetry installed successfully${NC}"
}

# Function to add PATH to shell config if not present
add_path_to_shell_config() {
    local shell_rc="$1"
    if [[ -f "$shell_rc" ]]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$shell_rc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$shell_rc"
            
            # If poetry was just installed, add it to PATH as well
            if [[ -d "$HOME/.poetry/bin" ]]; then
                if ! grep -q 'export PATH="$HOME/.poetry/bin:$PATH"' "$shell_rc"; then
                    echo 'export PATH="$HOME/.poetry/bin:$PATH"' >> "$shell_rc"
                fi
            fi
            return 0
        fi
    fi
    return 1
}

# Function to setup shell PATH
setup_shell_path() {
    echo -e "${BLUE}Setting up shell PATH...${NC}"
    
    # Create the bin directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
    
    # Add to shell config files if needed
    path_added=0
    shell_updated=""
    
    # Detect shell and update appropriate config
    if [[ "$SHELL" == *"zsh"* ]]; then
        if add_path_to_shell_config "$HOME/.zshrc"; then
            path_added=1
            shell_updated=".zshrc"
        fi
    elif [[ "$SHELL" == *"bash"* ]]; then
        if add_path_to_shell_config "$HOME/.bashrc"; then
            path_added=1
            shell_updated=".bashrc"
        fi
    else
        # Try to update common shell config files
        for config in ".bashrc" ".zshrc" ".profile"; do
            if add_path_to_shell_config "$HOME/$config"; then
                path_added=1
                shell_updated="$config"
                break
            fi
        done
    fi
    
    if [[ $path_added -eq 1 ]]; then
        echo -e "${GREEN}✓ Added required directories to PATH in ${shell_updated}${NC}"
    else
        echo -e "${YELLOW}! PATH already configured or could not identify shell${NC}"
        echo -e "${YELLOW}! Make sure ${INSTALL_DIR} is in your PATH${NC}"
    fi
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "${BLUE}Installing CLI dependencies...${NC}"
    
    cd "${CLI_DIR}" || {
        echo -e "${RED}Error: Could not change to CLI directory: ${CLI_DIR}${NC}"
        exit 1
    }
    
    # Install dependencies using poetry
    poetry install --no-interaction --no-ansi || {
        echo -e "${RED}Error: Failed to install dependencies${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
}

# Function to create CLI launcher
create_cli_launcher() {
    echo -e "${BLUE}Creating CLI launcher...${NC}"
    
    # Create the wrapper script
    cat > "$INSTALL_DIR/hs-cli" << EOL
#!/usr/bin/env bash
cd "${CLI_DIR}" || { echo "Error: Could not change to CLI directory"; exit 1; }
poetry run python main.py "\$@"
EOL

    # Make the wrapper script executable
    chmod +x "$INSTALL_DIR/hs-cli" || {
        echo -e "${RED}Error: Could not make launcher executable${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✓ CLI launcher created at ${INSTALL_DIR}/hs-cli${NC}"
}

# Main installation flow
main() {
    echo -e "${BLUE}Starting installation...${NC}"
    
    # Check Python version
    check_python_version
    
    # Check for Poetry and install if needed
    if ! command_exists poetry; then
        echo -e "${YELLOW}Poetry not found. Installing...${NC}"
        install_poetry
    else
        echo -e "${GREEN}✓ Poetry is already installed${NC}"
    fi
    
    # Setup shell PATH
    setup_shell_path
    
    # Create CLI launcher
    create_cli_launcher
    
    # Install dependencies
    install_dependencies
    
    # Final message
    echo -e "\n${GREEN}${BOLD}Installation complete!${NC}"
    echo -e "${GREEN}You can now use ${BOLD}hs-cli${NC}${GREEN} command from your terminal.${NC}"
    
    if [[ $path_added -eq 1 ]]; then
        echo -e "${YELLOW}Note: Please restart your terminal or run:${NC}"
        echo -e "${BOLD}source ~/${shell_updated}${NC}"
    fi
    
    # Test command
    echo -e "\n${BLUE}You can test your installation with:${NC}"
    echo -e "${BOLD}hs-cli --version${NC}"
}

# Run the main installation
main