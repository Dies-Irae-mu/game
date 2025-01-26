from evennia.utils import evtable
from evennia.commands.default.muxcommand import MuxCommand
from world.wod20th.utils.language_data import AVAILABLE_LANGUAGES
from evennia.utils.search import search_object
from world.wod20th.utils.formatting import header, footer, divider, format_stat
from world.wod20th.utils.ansi_utils import wrap_ansi
from evennia.utils.ansi import ANSIString

# This dictionary should be populated with all available languages
class CmdLanguage(MuxCommand):
    """
    Set your speaking language, view known languages, or add a new language.

    Usage:
      +language
      +language <language>
      +language none
      +language/add <language>
      +language/all
      +language/set <character>=<language1>,<language2>,...  (Staff only)
      +language/rem <language>         (Remove a language from yourself)
      +language/rem <name>=<language>  (Staff only - Remove from others)
      +language/view <name>            (Staff only - View character's languages)

    Examples:
      +language
      +language Spanish
      +language none
      +language/add French
      +language/all
      +language/set Bob=English,Spanish,French
      +language/view Bob
    """

    key = "+language"
    aliases = ["+lang", "+languages"]
    locks = "cmd:all()"
    help_category = "RP Commands"
    
    def func(self):
        """Execute command."""
        if "check" in self.switches:
            # Add a new switch to manually check and adjust languages
            self.validate_languages()
            self.list_languages()
            return
        
        if not self.args and not self.switches:
            # Display languages
            self.list_languages()
            return
        
        if "native" in self.switches:
            if not self.args:
                self.caller.msg("Usage: +language/native <language>")
                return
            
            # Only allow setting native language if not approved
            if self.caller.db.approved:
                self.caller.msg("You can only set your native language during character generation.")
                return
            
            language = self.args.strip().title()
            if language not in self.caller.get_languages():
                self.caller.msg(f"You must know a language before setting it as native. Use +language/add {language} first.")
                return
            
            # Store the old native language
            old_native = self.caller.db.native_language or "English"
            
            # If switching to English, check if we need to remove a language
            if language == "English":
                languages = self.caller.get_languages()
                merits = self.caller.db.stats.get('merits', {})
                language_merit_points = 0
                natural_linguist = False
                
                # Calculate available points
                for category in merits:
                    category_merits = merits[category]
                    if any(merit.lower().replace(' ', '') == 'naturallinguist' 
                          for merit in category_merits.keys()):
                        natural_linguist = True
                        break
                
                for category in merits:
                    category_merits = merits[category]
                    for merit_name, merit_data in category_merits.items():
                        if merit_name == 'Language':
                            base_points = merit_data.get('perm', 0)
                            language_merit_points = base_points * 2 if natural_linguist else base_points
                            break
                        elif merit_name.startswith('Language('):
                            base_points = merit_data.get('perm', 0)
                            points = base_points * 2 if natural_linguist else base_points
                            language_merit_points += points
                
                # Calculate used points after switch
                used_languages = len(languages) - 1  # -1 for English
                
                # If switching to English would put us over points, remove the last added language
                if used_languages > language_merit_points:
                    if len(languages) > 1:  # Make sure we don't remove English
                        last_language = languages[-1]
                        languages.remove(last_language)
                        self.caller.db.languages = languages
                        self.caller.msg(f"Removed {last_language} to stay within language point limits.")
            
            # Set the new native language
            self.caller.db.native_language = language
            self.caller.msg(f"You have set {language} as your native language.")
            
            # Show updated language list
            self.list_languages()
            return

        if "set" in self.switches:
            self.do_set_languages()
        elif "rem" in self.switches:
            self.remove_language()
        elif "all" in self.switches:
            self.list_all_languages()
        elif "view" in self.switches:
            self.view_character_languages()
        elif not self.args:
            self.list_languages()
        elif "add" in self.switches:
            self.add_language()
        elif self.args.lower() == "none":
            self.set_speaking_language(None)
        else:
            self.set_speaking_language(self.args.lower().capitalize())

    def list_languages(self):
        """Display the character's known languages and current speaking language."""
        languages = self.caller.get_languages()
        current = self.caller.get_speaking_language()
        
        # Create the output using raw strings
        divider_line = "-" * 78
        
        main_header = "|b< |yLanguages|n |b>"
        known_header = "|b< |yKnown Languages|n |b>"
        speaking_header = "|b< |yCurrently Speaking|n |b>"
        merit_header = "|b< |yMerit Points|n |b>"
        
        # Strip ANSI codes for length calculation
        main_length = len(ANSIString(main_header).clean())
        known_length = len(ANSIString(known_header).clean())
        speaking_length = len(ANSIString(speaking_header).clean())
        merit_length = len(ANSIString(merit_header).clean())
        
        main_padding = (78 - main_length) // 2
        known_padding = (78 - known_length) // 2
        speaking_padding = (78 - speaking_length) // 2
        merit_padding = (78 - merit_length) // 2
        
        output = [
            f"|b{'-' * main_padding}{main_header}{'-' * (78 - main_padding - main_length)}|n",
            f"|b{'-' * known_padding}{known_header}{'-' * (78 - known_padding - known_length)}|n",
        ]
        
        # Format languages list with wrapping
        if languages:
            wrapped_languages = wrap_ansi(f"|w{', '.join(languages)}|n", width=76, left_padding=0)
            output.append(wrapped_languages)
        else:
            output.append("None")
        
        # Add current speaking language
        output.extend([
            f"|b{'-' * speaking_padding}{speaking_header}{'-' * (78 - speaking_padding - speaking_length)}|n",
            current if current else "None"
        ])

        # Merit points section
        merits = self.caller.db.stats.get('merits', {})
        language_merit_points = 0
        natural_linguist = False
        native_language = self.caller.db.native_language or "English"  # Default to English if not set
        
        # Merit checks (same as before)
        for category in merits:
            category_merits = merits[category]
            if any(merit.lower().replace(' ', '') == 'naturallinguist' 
                  for merit in category_merits.keys()):
                natural_linguist = True
                break
        
        for category in merits:
            category_merits = merits[category]
            for merit_name, merit_data in category_merits.items():
                if merit_name == 'Language':
                    base_points = merit_data.get('perm', 0)
                    language_merit_points = base_points * 2 if natural_linguist else base_points
                    break
                elif merit_name.startswith('Language('):
                    base_points = merit_data.get('perm', 0)
                    points = base_points * 2 if natural_linguist else base_points
                    language_merit_points += points

        if language_merit_points > 0:
            # Calculate used languages, excluding English and native language
            used_languages = len(languages)
            if "English" in languages:
                used_languages -= 1  # English is always free
            if native_language in languages and native_language != "English":
                used_languages -= 1  # Native language is also free
            
            points_remaining = language_merit_points - used_languages

            output.extend([
                f"|b{'-' * merit_padding}{merit_header}{'-' * (78 - merit_padding - merit_length)}|n",
                f"Total points: {language_merit_points} ({language_merit_points//2 if natural_linguist else language_merit_points} from Language merit{' x2 from Natural Linguist' if natural_linguist else ''})",
                f"Native language: {native_language}",
                f"Languages used: {used_languages}",
                f"Points remaining: {points_remaining}"
            ])
        else:
            output.extend([
                f"|b{'-' * merit_padding}{merit_header}{'-' * (78 - merit_padding - merit_length)}|n",
                f"Native language: {native_language}"
            ])
        
        output.append(f"|b{'-' * 78}|n")
        
        # Send only the formatted output
        self.caller.msg("\n".join(output))

    def set_speaking_language(self, language):
        try:
            self.caller.set_speaking_language(language)
            if language:
                self.caller.msg(f"|cLANGUAGE>|n Now speaking in |w{language}|n.")
            else:
                self.caller.msg("|cLANGUAGE>|n You are no longer speaking in any specific language.")
        except ValueError as e:
            self.caller.msg(str(e))

    def add_language(self):
        """Add a new language to the character."""
        if not self.args:
            self.caller.msg("Usage: +language/add <language>")
            return

        language = self.args.strip().title()
        if language not in AVAILABLE_LANGUAGES.values():
            self.caller.msg(f"'{language}' is not a valid language. Use +languages/list to see available languages.")
            return

        languages = self.caller.get_languages()
        if language in languages:
            self.caller.msg(f"You already know {language}.")
            return

        # Get native language
        native_language = self.caller.db.native_language or "English"

        # Calculate current language points used
        used_languages = len(languages)
        if "English" in languages:
            used_languages -= 1  # English is always free
        if native_language in languages and native_language != "English":
            used_languages -= 1  # Native language is free

        # Check if they have enough points
        merits = self.caller.db.stats.get('merits', {})
        language_merit_points = 0
        natural_linguist = False

        # Check for Natural Linguist
        for category in merits:
            category_merits = merits[category]
            if any(merit.lower().replace(' ', '') == 'naturallinguist' 
                  for merit in category_merits.keys()):
                natural_linguist = True
                break

        # Calculate total available points
        for category in merits:
            category_merits = merits[category]
            for merit_name, merit_data in category_merits.items():
                if merit_name == 'Language':
                    base_points = merit_data.get('perm', 0)
                    language_merit_points = base_points * 2 if natural_linguist else base_points
                    break
                elif merit_name.startswith('Language('):
                    base_points = merit_data.get('perm', 0)
                    points = base_points * 2 if natural_linguist else base_points
                    language_merit_points += points

        if used_languages >= language_merit_points:
            self.caller.msg("You don't have enough language points remaining.")
            return

        # Add the language
        languages.append(language)
        self.caller.db.languages = languages
        
        # Calculate points used for display
        points_used = used_languages + 1  # +1 for the new language
        if language == native_language:
            points_used -= 1  # Don't count if it's the native language
        
        self.caller.msg(f"You have learned {language}. ({points_used}/{language_merit_points} additional languages used)")

    def do_set_languages(self):
        """
        Staff command to set languages on a character.
        Usage: +language/set <character>=<language1>,<language2>,...
        Adds specified languages to character's existing languages.
        """
        if not self.caller.check_permstring("Developer"):
            self.caller.msg("You don't have permission to set languages.")
            return
            
        if not self.lhs or not self.rhs:
            self.caller.msg("Usage: +language/set <character>=<language1>,<language2>,...\n"
                          "Example: +language/set Bob=French,Spanish")
            return
            
        # Search for both online and offline characters
        matches = search_object(self.lhs.strip(), 
                                     typeclass='typeclasses.characters.Character')
        if not matches:
            self.caller.msg(f"Could not find character '{self.lhs}'.")
            return
        target = matches[0]
            
        current_languages = target.get_languages()
        new_languages = current_languages.copy()
        invalid_languages = []
        
        # Process each language
        for lang in self.rhs.split(','):
            lang = lang.strip()
            
            if not lang or lang.lower() == "english":  # Skip empty or English
                continue
                
            # Try to find the proper case version
            found = False
            for available_lang in AVAILABLE_LANGUAGES.values():
                if available_lang.lower() == lang.lower():
                    if available_lang not in new_languages:
                        new_languages.append(available_lang)
                    found = True
                    break
                    
            if not found:
                invalid_languages.append(lang)
        
        if invalid_languages:
            self.caller.msg(f"Warning: The following languages were not recognized: {', '.join(invalid_languages)}\n"
                          f"Available languages are: {', '.join(AVAILABLE_LANGUAGES.values())}")
            return
            
        # Set the languages
        target.db.languages = new_languages
        
        self.caller.msg(f"Set {target.name}'s languages to: {', '.join(new_languages)}")
        target.msg(f"Your known languages have been set to: {', '.join(new_languages)}")

    def list_all_languages(self):
        """Display all available languages organized by region."""
        # Define categories and their languages
        categories = {
            "San Diego Common Languages": [
                "Spanish", "Filipino/Tagalog", "Chinese", "Vietnamese", "Korean", "Japanese", 
                "Mon-Khmer (Cambodian)", "Hmong", "Thai", "Laotian"
            ],

            "Major World Languages": [
                "Arabic", "Bengali", "Mandarin", "English", "French", 
                "German", "Hindi", "Indonesian", "Italian", "Japanese", "Korean",
                "Farsi", "Portuguese", "Russian", "Spanish", "Turkish",
                "Urdu"
            ],
            "African Languages": [
                "Amharic", "Hausa", "Igbo", "Lingala", "Oromo", "Somali",
                "Swahili", "Twi", "Wolof", "Yoruba", "Zulu", "Afrikaans", "Bambara", 
                "Bemba", "Chichewa", "Ganda", "Kikuyu", "Kinyarwanda", "Luganda", 
                "Luo", "Makonde", "Maltese", "Mbumba", "Ndebele", "Nyanja", "Shona", 
                "Swati", "Tswana", "Venda", "Xhosa", "Zulu"
            ],
            "European Languages": [
                "Bosnian", "Bulgarian", "Croatian", "Czech", "Danish", "Dutch",
                "Finnish", "Greek", "Hungarian", "Norwegian", "Polish", "Romanian",
                "Serbian", "Swedish", "Ukrainian", "Albanian", "Armenian", "Azerbaijani", 
                "Belarusian", "Bosnian", "Bulgarian", "Croatian", "Czech", "Danish", 
                "Dutch", "Estonian", "Finnish", "French", "German", "Greek", "Hungarian", 
                "Icelandic", "Irish", "Italian", "Latvian", "Lithuanian", "Macedonian", 
                "Maltese", "Moldovan", "Montenegrin", "Norwegian", "Polish", "Romanian", 
                "Serbian", "Slovak", "Slovenian", "Swedish", "Ukrainian"
            ],
            "Asian Languages": [
                "Burmese", "Cantonese", "Gujarati", "Khmer", "Lao",
                "Malay", "Punjabi", "Tamil", "Telugu", "Thai"
            ],
            "Middle Eastern Languages": [
                "Hebrew", "Kurdish", "Armenian", "Syriac", "Pashto"
            ],
            "Indigenous American Languages": [
                "Navajo", "Quechua", "Inuit", "Apache", "Cherokee", "Chamorro", "Chickasaw", 
                "Choctaw", "Comanche", "Cree", "Haida", "Haudenosaunee", "Iroquois", "Kiowa", 
                "Lakota", "Maya", "Navajo", "Pueblo", "Tlingit", "Turtle", "Yaqui", "Zuni"
            ],
            "Pacific Languages": [
                "Hawaiian", "Maori", "Tagalog", "Samoan", "Tahitian", "Tongan", "Fijian"
            ]
        }
        
        # Create the display table
        from evennia.utils import evtable
        
        # Header
        self.caller.msg("|wAvailable Languages:|n")
        self.caller.msg("=" * 78)
        
        # Display each category
        for category_name, languages in categories.items():
            if languages:  # Only show categories that have languages
                self.caller.msg(f"\n|y{category_name}:|n")
                
                # Sort languages alphabetically within each category
                languages.sort()
                
                # Create columns (3 columns of approximately equal size)
                table = evtable.EvTable(border=None)
                col_width = 25  # Adjust this if needed
                
                # Split languages into columns
                col1 = languages[::3]
                col2 = languages[1::3]
                col3 = languages[2::3]
                
                # Add columns to table
                table.add_column(*col1, width=col_width)
                if col2:  # Only add column if there are languages for it
                    table.add_column(*col2, width=col_width)
                if col3:  # Only add column if there are languages for it
                    table.add_column(*col3, width=col_width)
                
                # Display the table
                self.caller.msg(table)
        
        self.caller.msg("\n" + "=" * 78)

    def remove_language(self):
        """
        Remove a language from a character.
        Players can only remove languages from themselves.
        Staff can remove languages from any character.
        """
        if not self.args:
            self.caller.msg("Usage: +language/rem <language> or +language/rem <name>=<language>")
            return

        # Check if this is a staff removing language from another player
        if "=" in self.args:
            if not self.caller.check_permstring("Developer"):
                self.caller.msg("Only staff are allowed to remove languages from other players.")
                return
            
            target_name, language = self.args.split("=", 1)
            matches = search_object(target_name.strip(), 
                                      typeclass='typeclasses.characters.Character')
            if not matches:
                self.caller.msg(f"Could not find character '{target_name}'.")
                return
            target = matches[0]
        else:
            target = self.caller
            language = self.args

        language = language.strip()
        
        # Can't remove English
        if language.lower() == "english":
            self.caller.msg("You cannot remove English.")
            return

        # Get current languages
        current_languages = target.get_languages()
        
        # Try to find the proper case version
        found = False
        for lang_key, proper_lang in AVAILABLE_LANGUAGES.items():
            if lang_key.lower() == language.lower():
                if proper_lang in current_languages:
                    current_languages.remove(proper_lang)
                    target.db.languages = current_languages
                    
                    # If they were speaking the removed language, reset to English
                    if target.get_speaking_language() == proper_lang:
                        target.db.speaking_language = "English"
                        target.msg(f"Your speaking language has been reset to English.")
                    
                    # Notify both staff and target
                    if target == self.caller:
                        self.caller.msg(f"You have removed {proper_lang} from your known languages.")
                    else:
                        self.caller.msg(f"You have removed {proper_lang} from {target.name}'s known languages.")
                        target.msg(f"{proper_lang} has been removed from your known languages.")
                else:
                    self.caller.msg(f"{target.name if target != self.caller else 'You'} does not know {proper_lang}.")
                found = True
                break
        
        if not found:
            self.caller.msg(f"Invalid language. Available languages are: {', '.join(AVAILABLE_LANGUAGES.values())}")

    def view_character_languages(self):
        """
        Staff command to view a character's languages.
        Usage: +language/view <character>
        """
        if not self.caller.check_permstring("Developer"):
            self.caller.msg("You don't have permission to view other characters' languages.")
            return

        if not self.args:
            self.caller.msg("Usage: +language/view <character>")
            return

        # Search for both online and offline characters
        matches = search_object(self.args.strip(), 
                              typeclass='typeclasses.characters.Character')
        if not matches:
            self.caller.msg(f"Could not find character '{self.args}'.")
            return
        
        target = matches[0]
        languages = target.get_languages()
        current = target.get_speaking_language()
        
        # Test line to check if ANY colors work
        self.caller.msg("|rTEST RED|n |bTEST BLUE|n |yTEST YELLOW|n")
        
        # Create the output using raw strings
        divider_line = "-" * 78
        
        output = [
            f"|b{divider_line}|n",
            f"|b{' ' * 30}< Languages >|n",
            f"|b{divider_line}|n",
            f"|b{' ' * 25}Known Languages|n",
            f"|b{divider_line}|n",
        ]
        
        # Format languages list with wrapping
        if languages:
            wrapped_languages = wrap_ansi(f"|y{', '.join(languages)}|n", width=76, left_padding=0)
            output.append(wrapped_languages)
        else:
            output.append("None")
        
        # Add current speaking language
        output.extend([
            f"|b{divider_line}|n",
            f"|b{' ' * 25}Currently Speaking|n",
            f"|b{divider_line}|n",
            current if current else "None"
        ])

        # Merit points section
        merits = target.db.stats.get('merits', {})
        language_merit_points = 0
        natural_linguist = False
        native_language = target.db.native_language or "English"
        
        # Check for Natural Linguist and Language merits
        for category in merits:
            category_merits = merits[category]
            if any(merit.lower().replace(' ', '') == 'naturallinguist' 
                  for merit in category_merits.keys()):
                natural_linguist = True
                break
        
        for category in merits:
            category_merits = merits[category]
            for merit_name, merit_data in category_merits.items():
                if merit_name == 'Language':
                    base_points = merit_data.get('perm', 0)
                    language_merit_points = base_points * 2 if natural_linguist else base_points
                    break
                elif merit_name.startswith('Language('):
                    base_points = merit_data.get('perm', 0)
                    points = base_points * 2 if natural_linguist else base_points
                    language_merit_points += points

        if language_merit_points > 0:
            output.extend([
                f"|b{divider_line}|n",
                f"|b{' ' * 25}Merit Points|n",
                f"|b{divider_line}|n",
                f"Total points: {language_merit_points} ({language_merit_points//2 if natural_linguist else language_merit_points} from Language merit{' x2 from Natural Linguist' if natural_linguist else ''})",
                f"Native language: {native_language}",
                f"Languages used: {len(languages) - 2}",  # -2 because English and native language are free
                f"Points remaining: {language_merit_points - (len(languages) - 2)}"
            ])
        else:
            output.extend([
                f"|b{divider_line}|n",
                f"|b{' ' * 25}Merit Points|n",
                f"|b{divider_line}|n",
                f"Native language: {native_language}"
            ])
        
        output.append(f"|b{divider_line}|n")
        
        # Send raw string first, then processed version
        raw_output = "\n".join(output)
        self.caller.msg(f"Raw output: {raw_output}")  # Debug line
        self.caller.msg(raw_output)

    def validate_languages(self, caller=None):
        """
        Validate and adjust languages based on current merit points.
        Returns True if languages were adjusted, False otherwise.
        """
        target = caller or self.caller
        languages = target.get_languages()
        native_language = target.db.native_language or "English"
        
        # Calculate available points
        merits = target.db.stats.get('merits', {})
        language_merit_points = 0
        natural_linguist = False
        
        # Check for Natural Linguist
        for category in merits:
            category_merits = merits[category]
            if any(merit.lower().replace(' ', '') == 'naturallinguist' 
                  for merit in category_merits.keys()):
                natural_linguist = True
                break
        
        # Calculate total available points
        for category in merits:
            category_merits = merits[category]
            for merit_name, merit_data in category_merits.items():
                if merit_name == 'Language':
                    base_points = merit_data.get('perm', 0)
                    language_merit_points = base_points * 2 if natural_linguist else base_points
                    break
                elif merit_name.startswith('Language('):
                    base_points = merit_data.get('perm', 0)
                    points = base_points * 2 if natural_linguist else base_points
                    language_merit_points += points
        
        # Calculate how many languages we can keep
        # Always keep English and native language
        allowed_languages = ["English"]
        if native_language != "English":
            allowed_languages.append(native_language)
        
        # Calculate how many additional languages we can keep
        additional_slots = language_merit_points
        
        # Add languages in order until we hit our limit
        languages_removed = []
        final_languages = allowed_languages.copy()
        
        for lang in languages:
            # Skip if it's already in our allowed list
            if lang in allowed_languages:
                continue
            
            # If we have slots available, add the language
            if additional_slots > 0:
                final_languages.append(lang)
                additional_slots -= 1
            else:
                languages_removed.append(lang)
        
        if languages_removed:
            # Update the character's languages
            target.db.languages = final_languages
            target.msg(f"Removed {', '.join(languages_removed)} to stay within language point limits.")
            return True
        
        return False

    def update_merit(self, merit_name, new_value):
        """Update a merit's value and validate languages if necessary."""
        # Store old values for comparison
        old_value = self.db.stats.get('merits', {}).get(merit_name, {}).get('perm', 0)
        had_natural_linguist = any(
            merit.lower().replace(' ', '') == 'naturallinguist'
            for category in self.db.stats.get('merits', {}).values()
            for merit in category.keys()
        )
        
        # If it's a language-related merit and the value decreased, validate languages
        if ((merit_name == 'Language' and new_value < old_value) or
            (merit_name == 'Natural Linguist' and had_natural_linguist) or
            (merit_name.startswith('Language(') and new_value < old_value)):
            from commands.CmdLanguage import CmdLanguage
            cmd = CmdLanguage()
            if cmd.validate_languages(self):
                cmd.list_languages()  # Only show if changes were made
