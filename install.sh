

set -e  # Exit on error

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

print_message() {
    echo -e "${BOLD}${GREEN}[INSTALLER]${NC} $1"
}

print_warning() {
    echo -e "${BOLD}${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${BOLD}${RED}[ERROR]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_python() {
    print_message "Checking Python installation..."
    if command_exists python3; then
        python_version=$(python3 --version)
        print_message "Found $python_version"
    else
        print_error "Python 3 is not installed. Please install Python 3 first."
        print_message "On Linux: apt install -y python3-full"
        print_message "On macOS: brew install python3"
        print_message "On Windows: Download from https://www.python.org/downloads/"
        exit 1
    fi
}

check_pip() {
    print_message "Checking pip installation..."
    if command_exists pip3 || command_exists pip; then
        print_message "pip is installed."
    else
        print_error "pip is not installed. Please install pip first."
        print_message "On Linux: apt install -y python3-pip"
        print_message "On macOS: brew install python3 (includes pip)"
        print_message "On Windows: pip should be included with Python installation"
        exit 1
    fi
}

check_git() {
    print_message "Checking git installation..."
    if command_exists git; then
        git_version=$(git --version)
        print_message "Found $git_version"
    else
        print_error "git is not installed. Please install git first."
        print_message "On Linux: apt install -y git"
        print_message "On macOS: brew install git"
        print_message "On Windows: Download from https://git-scm.com/download/win"
        exit 1
    fi
}

check_evennia() {
    print_message "Checking Evennia installation..."
    if command_exists evennia; then
        evennia_version=$(evennia --version)
        print_message "Found Evennia $evennia_version"
        return 0
    else
        print_warning "Evennia is not installed. We'll install it for you."
        return 1
    fi
}

install_evennia() {
    print_message "Installing Evennia..."
    pip install evennia
    if [ $? -ne 0 ]; then
        print_error "Failed to install Evennia. Please check your internet connection and try again."
        exit 1
    fi
    print_message "Evennia installed successfully."
}

install_dependencies() {
    print_message "Installing required dependencies..."
    pip install ephem markdown2 pillow requests
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
    print_message "Dependencies installed successfully."
}

create_evennia_game() {
    local game_name=$1
    print_message "Creating a new Evennia game: $game_name"
    
    if [ -d "$game_name" ]; then
        print_warning "A directory named '$game_name' already exists."
        read -p "Do you want to use this existing directory? (y/n): " use_existing
        if [[ $use_existing != "y" && $use_existing != "Y" ]]; then
            print_error "Installation aborted. Please choose a different game name."
            exit 1
        fi
    else
        evennia --init $game_name
        if [ $? -ne 0 ]; then
            print_error "Failed to create a new Evennia game. Please check the error message above."
            exit 1
        fi
    fi
    
    print_message "Evennia game created successfully."
}

clone_dies_irae() {
    local game_dir=$1
    print_message "Cloning Dies Irae repository into $game_dir..."
    
    mkdir -p temp_dies_irae
    git clone https://github.com/Dies-Irae-mu/game.git temp_dies_irae
    if [ $? -ne 0 ]; then
        print_error "Failed to clone Dies Irae repository. Please check your internet connection and try again."
        rm -rf temp_dies_irae
        exit 1
    fi
    
    print_message "Copying Dies Irae files to $game_dir..."
    cp -r temp_dies_irae/* $game_dir/
    if [ $? -ne 0 ]; then
        print_error "Failed to copy Dies Irae files to $game_dir."
        rm -rf temp_dies_irae
        exit 1
    fi
    
    rm -rf temp_dies_irae
    print_message "Dies Irae repository cloned and copied successfully."
}

update_settings() {
    local game_dir=$1
    local settings_file="$game_dir/server/conf/settings.py"
    
    print_message "Updating settings.py to include required apps..."
    
    if [ ! -f "$settings_file" ]; then
        print_error "settings.py not found at $settings_file."
        exit 1
    fi
    
    if grep -q "world.wod20th" "$settings_file"; then
        print_warning "INSTALLED_APPS already contains required apps."
    else
        echo '
INSTALLED_APPS += (
    "world.wod20th",
    "wiki",
    "world.jobs",
    "web.character",
    "world.plots",
    "world.hangouts",
    "world.groups",
    "world.equipment",
)' >> "$settings_file"
        
        if [ $? -ne 0 ]; then
            print_error "Failed to update settings.py."
            exit 1
        fi
        
        print_message "settings.py updated successfully."
    fi
}

clear_migrations() {
    local game_dir=$1
    print_message "Clearing migration files..."
    
    find "$game_dir/world" -path "*/migrations/*.py" -not -name "__init__.py" -delete
    
    print_message "Migration files cleared successfully."
}

run_migrations() {
    local game_dir=$1
    print_message "Running database migrations..."
    
    cd "$game_dir"
    
    print_message "Running initial migration..."
    evennia migrate
    if [ $? -ne 0 ]; then
        print_error "Failed to run initial migration. Please check the error message above."
        exit 1
    fi
    
    print_message "Making migrations for the apps..."
    evennia makemigrations
    if [ $? -ne 0 ]; then
        print_error "Failed to make migrations. Please check the error message above."
        exit 1
    fi
    
    print_message "Running migrations again..."
    evennia migrate
    if [ $? -ne 0 ]; then
        print_error "Failed to run migrations. Please check the error message above."
        exit 1
    fi
    
    print_message "Database migrations completed successfully."
}

load_wod_stats() {
    local game_dir=$1
    print_message "Loading WoD 20th stats..."
    
    cd "$game_dir"
    
    evennia load_wod20th_stats --dir data/
    if [ $? -ne 0 ]; then
        print_error "Failed to load WoD 20th stats. Please check the error message above."
        exit 1
    fi
    
    print_message "WoD 20th stats loaded successfully."
}

start_game() {
    local game_dir=$1
    print_message "Starting the game..."
    
    cd "$game_dir"
    
    evennia start
    if [ $? -ne 0 ]; then
        print_error "Failed to start the game. Please check the error message above."
        exit 1
    fi
    
    print_message "Game started successfully."
}

install_dies_irae() {
    local game_name=$1
    
    print_message "Starting Dies Irae installation..."
    
    check_python
    check_pip
    check_git
    
    check_evennia || install_evennia
    
    install_dependencies
    
    create_evennia_game "$game_name"
    
    clone_dies_irae "$game_name"
    
    update_settings "$game_name"
    
    clear_migrations "$game_name"
    
    run_migrations "$game_name"
    
    load_wod_stats "$game_name"
    
    echo ""
    echo -e "${BOLD}${GREEN}==================================================${NC}"
    echo -e "${BOLD}${GREEN}Dies Irae installation completed successfully!${NC}"
    echo -e "${BOLD}${GREEN}==================================================${NC}"
    echo ""
    echo -e "${BOLD}Your game is now running. You can access it at:${NC}"
    echo -e "Web client: ${BOLD}http://localhost:4001${NC}"
    echo -e "Telnet: ${BOLD}localhost:4000${NC}"
    echo ""
    echo -e "${BOLD}To stop the game:${NC} cd $game_name && evennia stop"
    echo -e "${BOLD}To start the game:${NC} cd $game_name && evennia start"
    echo ""
    echo -e "${BOLD}Enjoy your World of Darkness MUSH!${NC}"
}

usage() {
    echo "Usage: $0 <game_name>"
    echo ""
    echo "This script installs Dies Irae, a World of Darkness MUSH, into a new Evennia game."
    echo ""
    echo "Arguments:"
    echo "  game_name    The name of the Evennia game to create"
    echo ""
    echo "Example:"
    echo "  $0 my_wod_game"
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

install_dies_irae "$1"
