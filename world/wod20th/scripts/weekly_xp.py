"""Weekly XP distribution script."""
from evennia.scripts.scripts import DefaultScript
from datetime import datetime, timezone
from decimal import Decimal
from evennia.utils import gametime
from typeclasses.characters import Character

class WeeklyXPScript(DefaultScript):
    """A script that runs weekly to award XP."""
    
    def at_script_creation(self):
        """Called when script is first created."""
        self.key = "WeeklyXP"
        self.desc = "Awards weekly XP to active characters"
        self.interval = 3600  # 1 hour in seconds
        self.persistent = True
        self.start_delay = True
        
    def at_start(self):
        """Called when script starts running."""
        try:
            self.ndb.next_repeat = gametime.gametime(absolute=True) + self.interval
        except Exception as e:
            print(f"Error in WeeklyXPScript at_start: {e}")
    
    def at_server_reload(self):
        """Called when server reloads."""
        try:
            # Clear any existing tasks
            if hasattr(self, 'task'):
                self.task.stop()
            # Don't save state during reload
            return
        except Exception as e:
            print(f"Error in WeeklyXPScript at_server_reload: {e}")
        
    def at_server_shutdown(self):
        """Called at server shutdown."""
        try:
            # Clear any existing tasks
            if hasattr(self, 'task'):
                self.task.stop()
            # Don't save state during shutdown
            return
        except Exception as e:
            print(f"Error in WeeklyXPScript at_server_shutdown: {e}")
            
    def _pause_task(self, auto_pause=False):
        """Override default pause behavior."""
        try:
            if hasattr(self, 'task'):
                self.task.stop()
            return
        except Exception as e:
            print(f"Error in WeeklyXPScript _pause_task: {e}")
            
    def at_repeat(self):
        """Called every hour to check if it's time to award XP."""
        now = datetime.now(timezone.utc)
        
        try:
            print(f"WeeklyXP script running at {now}")
            self.ndb.next_repeat = gametime.gametime(absolute=True) + self.interval
            
            if True:  # For testing, always run
                print("Time check passed, processing characters...")
                
                characters = Character.objects.filter(
                    db_typeclass_path__contains='characters.Character'
                )
                print(f"Found {characters.count()} characters to process")
                
                base_xp = Decimal('4.00')
                awarded_count = 0
                
                for char in characters:
                    try:
                        print(f"\nProcessing character: {char.name}")
                        
                        if hasattr(char, 'check_permstring') and char.check_permstring("builders"):
                            print(f"Skipping {char.name} - is staff")
                            continue
                        
                        xp_data = char.attributes.get('xp', default=None)
                        print(f"XP data type: {type(xp_data)}")
                        print(f"XP data content: {xp_data}")
                        
                        if not xp_data:
                            print(f"{char.name} has no xp attribute")
                            continue
                        
                        if hasattr(xp_data, 'get'):
                            scenes_this_week = int(xp_data.get('scenes_this_week', 0))
                        else:
                            print(f"{char.name}'s xp is not a dict-like object")
                            continue
                            
                        print(f"{char.name} has {scenes_this_week} scenes this week")
                        
                        if scenes_this_week > 0:
                            print(f"Attempting to award XP to {char.name}")
                            
                            # Update XP values directly
                            xp_data['total'] = xp_data.get('total', Decimal('0.00')) + base_xp
                            xp_data['current'] = xp_data.get('current', Decimal('0.00')) + base_xp
                            xp_data['ic_earned'] = xp_data.get('ic_earned', Decimal('0.00')) + base_xp
                            xp_data['scenes_this_week'] = 0
                            xp_data['last_scene'] = now
                            
                            # Save the updated XP data
                            char.attributes.add('xp', xp_data)
                            char.save()
                            print(f"Successfully awarded {base_xp} XP to {char.name}")
                            print(f"New XP data: {xp_data}")
                            awarded_count += 1
                        else:
                            print(f"Skipping {char.name} - no scenes this week")
                            
                    except Exception as e:
                        print(f"Error processing character {char}: {str(e)}")
                        continue
                
                print(f"\nWeekly XP distribution completed. Awarded XP to {awarded_count} active characters.")
                
        except Exception as e:
            print(f"Error during XP distribution: {str(e)}")
            return 