#!/usr/bin/env python
import os
import shutil
import sys
import stat

def setup_git_hooks():
    """Set up git hooks for development."""
    hooks_dir = os.path.join('.git', 'hooks')
    if not os.path.exists(hooks_dir):
        print("Error: .git/hooks directory not found. Are you in a git repository?")
        sys.exit(1)

    # Get the absolute path to the Scripts directory
    scripts_dir = os.path.abspath(os.path.dirname(__file__))

    # Create hook files
    hooks = {
        'pre-commit': f'''@echo off
python "{os.path.join(scripts_dir, 'pre-commit.py')}"
''',
        'post-merge': f'''@echo off
python "{os.path.join(scripts_dir, 'post-merge.py')}"
''',
        'post-checkout': f'''@echo off
python "{os.path.join(scripts_dir, 'post-checkout.py')}"
'''
    }

    # Create the hook files
    for hook_name, hook_content in hooks.items():
        # Create the .cmd file
        cmd_path = os.path.join(hooks_dir, f"{hook_name}.cmd")
        with open(cmd_path, 'w') as f:
            f.write(hook_content)

def create_settings_template():
    """Create settings.py.template from settings.py if it doesn't exist."""
    settings_path = os.path.join('server', 'conf', 'settings.py')
    template_path = os.path.join('server', 'conf', 'settings.py.template')
    
    if not os.path.exists(template_path):
        if os.path.exists(settings_path):
            shutil.copy2(settings_path, template_path)
            print("Created settings.py.template from settings.py")
        else:
            print("Warning: settings.py not found. Cannot create template.")

def setup_settings():
    """Set up settings.py from template if it doesn't exist."""
    settings_path = os.path.join('server', 'conf', 'settings.py')
    template_path = os.path.join('server', 'conf', 'settings.py.template')
    
    if not os.path.exists(settings_path):
        if os.path.exists(template_path):
            # Ensure the directory exists
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            shutil.copy2(template_path, settings_path)
            print("Created settings.py from template")
        else:
            print("Error: Neither settings.py nor settings.py.template found.")
            sys.exit(1)

def main():
    print("Setting up development environment...")
    setup_git_hooks()
    create_settings_template()
    setup_settings()
    print("Setup complete!")

if __name__ == '__main__':
    main() 