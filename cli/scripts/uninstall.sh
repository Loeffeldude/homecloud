#!/usr/bin/env bash

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════╗"
echo "║          HomeCloud CLI Uninstaller            ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to clean PATH in shell config
clean_path_in_shell_config() {
    local shell_rc="$1"
    if [ -f "$shell_rc" ]; then
        # Remove our PATH additions
        sed -i.bak '/export PATH="\$HOME\/\.local\/bin:\$PATH"/d' "$shell_rc"
        sed -i.bak '/export PATH="\$HOME\/\.poetry\/bin:\$PATH"/d' "$shell_rc"
        echo -e "${GREEN}✓ Cleaned PATH settings in ${shell_rc}${NC}"
    fi
}

# Main uninstallation process
main() {
    echo -e "${BLUE}Starting uninstallation...${NC}"
    
    # Remove the CLI script
    if [ -f "$HOME/.local/bin/hs-cli" ]; then
        rm "$HOME/.local/bin/hs-cli"
        echo -e "${GREEN}✓ Removed hs-cli script${NC}"
    else
        echo -e "${YELLOW}! hs-cli script not found${NC}"
    fi
    
    # Remove PATH additions from shell config files
    for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        clean_path_in_shell_config "$rc_file"
    done
    
    # Ask if user wants to remove Poetry
    echo -e "${YELLOW}Do you want to remove Poetry? (y/N)${NC}"
    read -r remove_poetry
    if [[ "$remove_poetry" =~ ^[Yy]$ ]]; then
        if [ -d "$HOME/.poetry" ]; then
            rm -rf "$HOME/.poetry"
            echo -e "${GREEN}✓ Removed Poetry${NC}"
        else
            echo -e "${YELLOW}! Poetry directory not found${NC}"
        fi
    fi
    
    echo -e "\n${GREEN}${BOLD}Uninstallation complete!${NC}"
    echo -e "${YELLOW}Please restart your terminal for changes to take effect.${NC}"
}

# Ask for confirmation
echo -e "${RED}This will uninstall the HomeCloud CLI (hs-cli).${NC}"
echo -e "${YELLOW}Are you sure you want to continue? (y/N)${NC}"
read -r confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
    main
else
    echo -e "${BLUE}Uninstallation cancelled.${NC}"
    exit 0
fi