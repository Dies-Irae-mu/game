This is the source code for Dies Irae, a World of Darkness MUSH set in the city of San Diego.

If you are downloading this with the intention of creating a new game, here's what you need to do from the jump:

1. Install python, if you're using linux, that's ```apt install -y python3-full```
2. Find your home directory (best not use your root directory if you have multiple coders; if it's just you, use the root directory) and create a virtual environment using python3 -m venv (name of your environment)
3. Launch the virtual environment (in Linux, it's 'source bin/env_name/activate').
4. Install Evennia using a virtual environment using 'pip install evennia'. It may ask you to install some dependencies.
5. Now type evennia --init (name of game). This will create a folder in your current directory with the same name as your name of game.
6. Navigate to that folder and hold up; download the Dies Irae files from github.
7.  Make sure to run through and change the MUSH name from Dies Irae to the name of your choosing. There are several files where you'll want to do this. In VSCode if you load up the diesirae code you can just do a find and replace for Dies Irae with whatever it is you're going to name the game. It doesn't change anything that's necessary for the game to function.
8. Include the following in INSTALLED_APPS in your settings.py file:
```
INSTALLED_APPS += (
    "world.wod20th",
    "wiki",
    "world.jobs",
    "web.character",
    "world.plots",
    "world.hangouts",
    "world.groups",
    "world.equipment",
)
```
9. If there are any residual migration files located in any of the folders in world/, be sure to clear those out (on linux, just rm *.py in the migration folders). 
10. Install the following modules with pip on your server:
```
pip install ephem
pip install markdown2
pip install pillow
pip install requests
```
11. Upload the Dies Irae files to your server using whatever means you would like, either via git branch or the dreaded SFTP. Replace the existing Evennia files with the ones from the Dies Irae github.
12. Now back on your Linux shell window, run 'evennia migrate', it should prompt you to create a new superuser. This is your #1 user.
13. After that, do 'evennia makemigrations' then 'evennia migrate' again. This will ensure that all of the apps are loaded in and set up in the database.
14. Run 'evennia start'
15. Login using your #1 username and password.
16. et voila, you now have a WoD game.

Then from there you can tweak things to your liking. For example, 'VALID_SPLATS' in the stat_mappings.py file in world/wod20th/utils is the base element that indicates what different superanatural types are available on your game. You can modify it to whichever splats you intend to use. 

Make sure to remove any data files that you don't need for the spheres that yo're running, but remember to save the 'vampire' files since those contain a lot of the base information. You don't *have* to do this, but it will save server space and make it so that running the load_wod20th_stats command is quicker, especially if you're not running a game with Shifters (there are around 2000 gifts).

Once you're happy with tweaking things, use the following command:

evennia load_wod20th_stats --dir data/

...and that will load in all of the data files. You should now be able to set up character sheets by typing +selfstat splat=(name of splat), so +selfstat splat=mage would load up a Mage: The Ascension character sheet.

If you are changing out what splats you allow, it's not necessary to remove the utils files from the world/wod20th/utils folder. In fact, it would be inadvisable to do so, since you'd have to refactor all of the command files that use those utility files. So long as you change the VALID_SPLATS, you shouldn't have any issues with people grabbing other splat abilities.

Some systems aren't fully complete and it would be suggested to remove them or remark them out of the default_cmdsets.py file:
- Combat
- Extended mail commands
