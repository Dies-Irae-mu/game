# Dies Irae Game

Dies Irae is a text-based multiplayer online game built using the Evennia MUD/MUSH engine.

## Getting Started

Follow these steps to set up your development environment.

### 1. Clone the Repository
First, clone the Dies Irae source code from GitHub:

```sh
git clone https://github.com/Dies-Irae-mu/game.git
cd game
```

### 2. Set Up Your Environment
Ensure you have Python and virtualenv installed, then proceed with setting up the environment.

```sh
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies
Install all required dependencies:

```sh
pip install -r requirements.txt
```

### 4. Configure Evennia
Copy the example settings file into place:

```sh
cp server/conf/settings.py.example server/conf/settings.py
```
> Alternatively, obtain the latest `settings.py` from the coding Discord.

### 5. Apply Migrations
Run database migrations:

```sh
evennia migrate
```

### 6. Start the Server
Start the Evennia server:

```sh
evennia start
```

### 7. Connect to the Game
Use a MUSH client to connect to your local server:

```
127.0.0.1:4201
```

## Common Issues & Fixes

### 1. Migration Errors
If you encounter migration errors, try the following:

```sh
rm -rf wiki/migrations
evennia makemigrations
evennia migrate
```

### 2. Virtual Environment Issues
If dependencies are missing, ensure your virtual environment is activated:

```sh
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Evennia Not Found
If `evennia` commands are not recognized, try reinstalling Evennia:

```sh
pip install evennia
```

---

For additional support, join our community on Discord.
