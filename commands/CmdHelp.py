"""
Custom help command with disambiguation support.

This command extends Evennia's default help command to show multiple matches
when a help query could refer to multiple entries.
"""

from evennia.commands.default.help import CmdHelp as DefaultCmdHelp, HelpCategory
from evennia.help.models import HelpEntry
from evennia.utils import evtable
from evennia.utils.utils import dedent, pad, format_grid
from evennia.utils.ansi import ANSIString
from evennia.help.utils import parse_entry_for_subcategories, help_search_with_index
import re

class CmdHelp(DefaultCmdHelp):
    """
    Get help on commands or topics.

    Usage:
      help
      help <topic or command>
      help <topic>/<subtopic>
      helpnum <topic>/<number>   - select from multiple matches by number

    This command shows help on commands and other topics.
    When multiple matches are found, it will show a disambiguation
    menu allowing you to choose which help entry to view.
    
    To select a specific entry from the disambiguation list, use
    the helpnum command with the format: helpnum topic/number
    Example: helpnum build/1

    Use 'help' alone to see all available help entries.
    """

    key = "help"
    aliases = ["?"]
    locks = "cmd:all()"
    help_category = "General"
    
    # Store last matches for number selection
    last_matches = []

    def format_matches(self, matches, key_and_aliases):
        """
        Format multiple matches into a table for disambiguation.

        Args:
            matches (list): List of help entries that matched
            key_and_aliases (set): Set of all command keys and aliases

        Returns:
            str: Formatted table of matches
        """
        # Store matches for later selection
        self.__class__.last_matches = matches
        
        table = evtable.EvTable(
            "|wNumber|n",
            "|wName|n",
            "|wCategory|n",
            "|wType|n",
            table=None,
            border="header",
            header_line_char="-",
            width=self.client_width()
        )

        for i, match in enumerate(matches, 1):
            name = self.strip_cmd_prefix(
                match.key if hasattr(match, 'key') else match.db_key,
                key_and_aliases
            )
            
            # Handle different types of help entries
            if isinstance(match, HelpCategory):
                category = str(match)
                entry_type = "Category"
            else:
                category = match.help_category if hasattr(match, 'help_category') else match.db_help_category
                entry_type = "Command" if hasattr(match, 'func') else "Help Entry"
            
            table.add_row(
                f"|w{str(i)}|n",
                f"|w{name}|n",
                f"|w{category}|n",
                f"|w{entry_type}|n"
            )

        return str(table)

    def format_help_entry(
        self,
        topic="",
        help_text="",
        aliases=None,
        suggested=None,
        subtopics=None,
        click_topics=True,
    ):
        """Format the help entry with custom colors."""
        total_width = 78
        
        # Header with topic name
        title = f" Help for {topic} "
        title_len = len(title)
        dash_count = (total_width - title_len) // 2
        start = f"{'|b-|n' * dash_count}|w{title}|n{'|b-|n' * (total_width - dash_count - title_len)}\n"

        if aliases:
            aliases = " |w(aliases: {}|w)|n".format("|w,|n ".join(f"|w{ali}|n" for ali in aliases))
        else:
            aliases = ""

        help_text = "\n" + dedent(help_text.strip("\n")) if help_text else ""

        if subtopics:
            # Subtopics section header
            subtitle = " |y Subtopics |n"
            subtitle_len = len(subtitle)
            dash_count = (total_width - subtitle_len) // 2
            subtopics_header = f"\n{'|b-|n' * dash_count}{subtitle}{'|b-|n' * (total_width - dash_count - subtitle_len)}\n"
            
            if click_topics:
                subtopics = [
                    f"|lchelp {topic}/{subtop}|lt|w{topic}/{subtop}|n|le" for subtop in subtopics
                ]
            else:
                subtopics = [f"|w{topic}/{subtop}|n" for subtop in subtopics]
            subtopics = f"{subtopics_header}  " + "\n  ".join(
                format_grid(
                    subtopics, width=self.client_width()
                )
            )
        else:
            subtopics = ""

        if suggested:
            # Suggestions section header
            sugg_title = " |y Suggestions |n"
            sugg_len = len(sugg_title)
            dash_count = (total_width - sugg_len) // 2
            sugg_header = f"\n{'|b-|n' * dash_count}{sugg_title}{'|b-|n' * (total_width - dash_count - sugg_len)}\n"
            
            suggested = sorted(suggested)
            if click_topics:
                suggested = [f"|lchelp {sug}|lt|w{sug}|n|le" for sug in suggested]
            else:
                suggested = [f"|w{sug}|n" for sug in suggested]
            suggested = f"{sugg_header}  " + "\n  ".join(
                format_grid(
                    suggested, width=self.client_width()
                )
            )
        else:
            suggested = ""

        # Footer
        end = f"\n{'|b-|n' * total_width}"

        partorder = (start, aliases, help_text, subtopics, suggested, end)

        return "\n".join(part.rstrip() for part in partorder if part)

    def format_help_index(
        self, cmd_help_dict=None, db_help_dict=None, title_lone_category=False, click_topics=True
    ):
        """Format the help index with custom colors."""
        total_width = 78
        help_index = ""
        cmd_grid = ""
        db_grid = ""

        if cmd_help_dict and any(cmd_help_dict.values()):
            # Commands section header
            cmd_title = " Commands "
            title_len = len(cmd_title)
            dash_count = (total_width - title_len) // 2
            sep1 = f"{'|b-|n' * dash_count}|y{cmd_title}|n{'|b-|n' * (total_width - dash_count - title_len)}\n"
            
            # Format commands by category
            cmd_sections = []
            for category in sorted(cmd_help_dict.keys()):
                entries = sorted(set(cmd_help_dict.get(category, [])))
                if entries:
                    # Category header
                    cat_title = f" {category.title()} "
                    cat_len = len(cat_title)
                    dash_count = (total_width - cat_len) // 2
                    cat_header = f"{'|b-|n' * dash_count}|y{cat_title}|n{'|b-|n' * (total_width - dash_count - cat_len)}"
                    
                    # Format entries in columns
                    if click_topics:
                        entries = [f"|lchelp {entry}|lt|w{entry}|n|le" for entry in entries]
                    else:
                        entries = [f"|w{entry}|n" for entry in entries]
                    
                    entry_lines = format_grid(entries, width=total_width - 4, sep="  ")
                    formatted_entries = "\n".join("  " + line for line in entry_lines)
                    
                    cmd_sections.append(f"{cat_header}\n{formatted_entries}")
            
            if cmd_sections:
                sections_text = "\n".join(cmd_sections)
                cmd_grid = sep1 + sections_text

        if db_help_dict and any(db_help_dict.values()):
            # Game & World section header
            db_title = " Game & World "
            title_len = len(db_title)
            dash_count = (total_width - title_len) // 2
            sep2 = f"\n{'|b-|n' * dash_count}|y{db_title}|n{'|b-|n' * (total_width - dash_count - title_len)}\n"
            
            # Format help entries
            db_sections = []
            for category in sorted(db_help_dict.keys()):
                entries = sorted(set(db_help_dict.get(category, [])))
                if entries:
                    if click_topics:
                        entries = [f"|lchelp {entry}|lt|w{entry}|n|le" for entry in entries]
                    else:
                        entries = [f"|w{entry}|n" for entry in entries]
                    
                    entry_lines = format_grid(entries, width=total_width - 4, sep="  ")
                    formatted_entries = "\n".join("  " + line for line in entry_lines)
                    db_sections.append(formatted_entries)
            
            if db_sections:
                sections_text = "\n".join(db_sections)
                db_grid = sep2 + sections_text

        # Combine sections
        if cmd_grid and db_grid:
            help_index = cmd_grid + db_grid
        else:
            help_index = cmd_grid or db_grid

        # Add footer if there's any content
        if help_index:
            help_index += f"\n{'|b-|n' * total_width}"
        
        return help_index

    def _group_by_category(self, help_dict, click_topics=True):
        """Helper method to group help entries by category with custom colors."""
        grid = []
        verbatim_elements = []
        total_width = 78

        if len(help_dict) == 1:
            # don't list categories if there is only one
            for category in help_dict:
                entries = sorted(set(help_dict.get(category, [])))
                if click_topics:
                    entries = [f"|lchelp {entry}|lt|w{entry}|n|le" for entry in entries]
                grid.extend(entries)
        else:
            for category in sorted(set(list(help_dict.keys()))):
                entries = sorted(set(help_dict.get(category, [])))
                if entries:
                    # Category header
                    category_str = f" {category.title()} "
                    title_len = len(category_str)
                    dash_count = (total_width - title_len) // 2
                    category_header = f"{'|b-|n' * dash_count}|y{category_str}|n{'|b-|n' * (total_width - dash_count - title_len)}"
                    grid.append(category_header)
                    verbatim_elements.append(len(grid) - 1)

                    # Format entries with proper indentation
                    if click_topics:
                        entries = [f"|lchelp {entry}|lt|w{entry}|n|le" for entry in entries]
                    else:
                        entries = [f"|w{entry}|n" for entry in entries]
                    
                    entry_lines = format_grid(entries, width=total_width - 4, sep="  ")
                    grid.extend("  " + line for line in entry_lines)

        return grid, verbatim_elements

    def remove_duplicates(self, matches):
        """Remove duplicate entries from matches list."""
        # Use a dictionary to track unique items by name + category
        unique_matches = {}
        
        for match in matches:
            if isinstance(match, HelpCategory):
                key = f"category:{match.key}"
            else:
                entry_key = match.key if hasattr(match, 'key') else match.db_key
                category = match.help_category if hasattr(match, 'help_category') else match.db_help_category
                key = f"{entry_key}:{category}"
            
            if key not in unique_matches:
                unique_matches[key] = match
                
        return list(unique_matches.values())

    def func(self):
        """Execute the help command with disambiguation support."""
        caller = self.caller
        query = self.topic
        
        if not query:
            # Show the help index
            super().func()
            return

        # Get all help entries - using the parent class methods to ensure compatibility
        cmd_help_topics, db_help_topics, file_help_topics = super().collect_topics(
            caller, mode="query"
        )

        # Get all keys and aliases for prefix stripping
        key_and_aliases = set()
        for cmd in cmd_help_topics.values():
            key_and_aliases.update(cmd._keyaliases)

        # Combine all help entries
        file_db_help_topics = {**file_help_topics, **db_help_topics}
        all_topics = {**file_db_help_topics, **cmd_help_topics}

        # Get all categories (using a set to prevent duplicates)
        all_categories = {
            HelpCategory(topic.help_category) for topic in all_topics.values()
        }
        
        # Remove duplicates from categories
        unique_categories = {}
        for cat in all_categories:
            if cat.key not in unique_categories:
                unique_categories[cat.key] = cat

        # Get all available help entries
        entries = list(all_topics.values()) + list(unique_categories.values())

        # First try exact match by key
        exact_matches = []
        for entry in entries:
            entry_key = entry.key if hasattr(entry, 'key') else entry.db_key
            if entry_key and entry_key.lower() == query.lower():
                exact_matches.append(entry)
                
        # Remove duplicates
        exact_matches = self.remove_duplicates(exact_matches)

        # If no exact matches, try partial key matches
        if not exact_matches:
            partial_matches = []
            for entry in entries:
                entry_key = entry.key if hasattr(entry, 'key') else entry.db_key
                if entry_key and query.lower() in entry_key.lower():
                    partial_matches.append(entry)
            
            # Remove duplicates
            partial_matches = self.remove_duplicates(partial_matches)
            
            # Store for later access
            self.__class__.last_matches = partial_matches
            
            if len(partial_matches) == 1:
                # Single partial match found
                exact_matches = partial_matches
            elif len(partial_matches) > 1:
                # Multiple partial matches - show disambiguation
                matches_table = self.format_matches(
                    partial_matches,
                    key_and_aliases
                )
                
                # Show disambiguation menu
                total_width = 78
                title = f" Multiple matches found for '{query}' "
                title_len = len(title)
                dash_count = (total_width - title_len) // 2
                header = f"\n{'|b-|n' * dash_count}|y{title}|n{'|b-|n' * (total_width - dash_count - title_len)}"
                footer = f"\n|wUse 'helpnum {query}/<number>' to view a specific entry.|n\n{'|b-|n' * total_width}"
                
                caller.msg(f"{header}\n{matches_table}{footer}")
                return
            else:
                # No partial matches, try fuzzy search as last resort
                matches, suggestions = help_search_with_index(
                    query,
                    entries,
                    suggestion_maxnum=self.suggestion_maxnum,
                    fields=[
                        {"field_name": "key", "boost": 10},
                        {"field_name": "aliases", "boost": 7}
                    ]
                )
                
                # Remove duplicates in matches
                matches = self.remove_duplicates(matches)
                
                # Store for later access
                self.__class__.last_matches = matches
                
                # Only use fuzzy matches if they match the key or aliases
                fuzzy_matches = []
                for match in matches:
                    entry_key = match.key if hasattr(match, 'key') else match.db_key
                    # Check if entry has aliases attribute before accessing it
                    has_aliases = hasattr(match, 'aliases') and match.aliases is not None
                    
                    if entry_key and (
                        query.lower() in entry_key.lower() or 
                        (has_aliases and any(query.lower() in alias.lower() for alias in match.aliases))
                    ):
                        fuzzy_matches.append(match)
                
                # Remove duplicates in fuzzy matches
                fuzzy_matches = self.remove_duplicates(fuzzy_matches)
                
                # Store for later access
                self.__class__.last_matches = fuzzy_matches
                
                if len(fuzzy_matches) == 1:
                    exact_matches = fuzzy_matches
                elif len(fuzzy_matches) > 1:
                    # Multiple fuzzy matches - show disambiguation
                    matches_table = self.format_matches(
                        fuzzy_matches,
                        key_and_aliases
                    )
                    
                    # Show disambiguation menu
                    total_width = 78
                    title = f" Multiple matches found for '{query}' "
                    title_len = len(title)
                    dash_count = (total_width - title_len) // 2
                    header = f"\n{'|b-|n' * dash_count}|y{title}|n{'|b-|n' * (total_width - dash_count - title_len)}"
                    footer = f"\n|wUse 'helpnum {query}/<number>' to view a specific entry.|n\n{'|b-|n' * total_width}"
                    
                    caller.msg(f"{header}\n{matches_table}{footer}")
                    return

        if not exact_matches:
            # No matches at all - show the standard no-match message
            super().func()
            return

        # Single match found - show it
        match = exact_matches[0]

        if isinstance(match, HelpCategory):
            # Category match - show its contents
            category = match.key
            category_lower = category.lower()
            cmds_in_category = [
                key for key, cmd in cmd_help_topics.items() 
                if category_lower == cmd.help_category.lower()
            ]
            topics_in_category = [
                key for key, topic in file_db_help_topics.items()
                if category_lower == topic.help_category.lower()
            ]
            output = self.format_help_index(
                {category: cmds_in_category},
                {category: topics_in_category},
                title_lone_category=True,
                click_topics=self.clickable_topics
            )
            self.msg_help(output)
            return

        # Command or help entry match
        if hasattr(match, 'func'):
            # Command match
            topic = match.key
            help_text = match.get_help(caller, self.cmdset)
            aliases = match.aliases
            suggested = []  # Don't show suggestions for exact matches
        else:
            # Database/file help match
            topic = match.key if hasattr(match, 'key') else match.db_key
            help_text = match.entrytext if hasattr(match, 'entrytext') else match.db_entrytext
            # Check if object has aliases attribute
            if hasattr(match, 'aliases'):
                aliases = match.aliases if isinstance(match.aliases, list) else match.aliases.all()
            else:
                aliases = []
            suggested = []  # Don't show suggestions for exact matches

        # Parse for subtopics
        subtopic_map = parse_entry_for_subcategories(help_text)
        help_text = subtopic_map[None]
        subtopic_index = [subtopic for subtopic in subtopic_map if subtopic is not None]

        # Handle subtopics if specified
        if self.subtopics:
            for subtopic_query in self.subtopics:
                if subtopic_query not in subtopic_map:
                    # Try fuzzy matching
                    fuzzy_match = False
                    for key in subtopic_map:
                        if key and key.startswith(subtopic_query):
                            subtopic_query = key
                            fuzzy_match = True
                            break
                    if not fuzzy_match:
                        for key in subtopic_map:
                            if key and subtopic_query in key:
                                subtopic_query = key
                                fuzzy_match = True
                                break
                    if not fuzzy_match:
                        checked_topic = topic + f"{self.subtopic_separator_char}{subtopic_query}"
                        output = self.format_help_entry(
                            topic=topic,
                            help_text=f"No help entry found for '{checked_topic}'",
                            subtopics=subtopic_index,
                            click_topics=self.clickable_topics
                        )
                        self.msg_help(output)
                        return

                subtopic_map = subtopic_map[subtopic_query]
                subtopic_index = [subtopic for subtopic in subtopic_map if subtopic is not None]
                topic = topic + f"{self.subtopic_separator_char}{subtopic_query}"
            help_text = subtopic_map[None]

        # Format and display the help entry
        topic = self.strip_cmd_prefix(topic, key_and_aliases)
        if self.subtopics:
            aliases = None
        else:
            aliases = [self.strip_cmd_prefix(alias, key_and_aliases) for alias in aliases]

        output = self.format_help_entry(
            topic=topic,
            help_text=help_text,
            aliases=aliases,
            subtopics=subtopic_index,
            suggested=suggested,
            click_topics=self.clickable_topics
        )
        self.msg_help(output)


class CmdHelpNum(CmdHelp):
    """
    View a specific help entry by number from the list of matches.

    Usage:
      helpnum <topic>/<number>

    This command is used to select a specific help entry from
    the disambiguation list shown by the help command.
    
    Example:
      help build         - Shows all matches for "build"
      helpnum build/1    - Shows the first entry from the matches for "build"
    """
    
    key = "helpnum"
    aliases = []
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the help number command."""
        caller = self.caller
        
        # Parse arguments
        if not self.args:
            caller.msg("You must specify a topic and a number. Example: helpnum build/1")
            return
            
        # Extract topic and number
        match = re.match(r"^(.+)/(\d+)$", self.args)
        if not match:
            caller.msg("Invalid format. Use: helpnum <topic>/<number>")
            return
            
        topic, num_str = match.groups()
        try:
            index = int(num_str)
        except ValueError:
            caller.msg("The number must be a valid integer.")
            return
            
        # Check if we have stored matches for this topic
        if not CmdHelp.last_matches:
            # No matches stored, attempt to run a regular help command first
            self.topic = topic
            self.subtopics = []
            super().func()
            
            # If that didn't generate matches, return
            if not CmdHelp.last_matches:
                caller.msg(f"No matches found for '{topic}'.")
                return
        
        # Check if the index is valid
        if index < 1 or index > len(CmdHelp.last_matches):
            caller.msg(f"Invalid selection. Please choose a number between 1 and {len(CmdHelp.last_matches)}.")
            return
            
        # Get the selected match
        match = CmdHelp.last_matches[index - 1]
        
        # Get all help entries for context
        cmd_help_topics, db_help_topics, file_help_topics = super().collect_topics(
            caller, mode="query"
        )
        
        # Get all keys and aliases for prefix stripping
        key_and_aliases = set()
        for cmd in cmd_help_topics.values():
            key_and_aliases.update(cmd._keyaliases)
            
        # Combine help entries for lookup
        file_db_help_topics = {**file_help_topics, **db_help_topics}
        
        # Handle the match based on its type
        if isinstance(match, HelpCategory):
            # Category match - show its contents
            category = match.key
            category_lower = category.lower()
            cmds_in_category = [
                key for key, cmd in cmd_help_topics.items() 
                if category_lower == cmd.help_category.lower()
            ]
            topics_in_category = [
                key for key, topic in file_db_help_topics.items()
                if category_lower == topic.help_category.lower()
            ]
            output = self.format_help_index(
                {category: cmds_in_category},
                {category: topics_in_category},
                title_lone_category=True,
                click_topics=self.clickable_topics
            )
            self.msg_help(output)
            return
        
        # Command or help entry match
        if hasattr(match, 'func'):
            # Command match
            topic = match.key
            help_text = match.get_help(caller, self.cmdset)
            aliases = match.aliases
            suggested = []  # Don't show suggestions for exact matches
        else:
            # Database/file help match
            topic = match.key if hasattr(match, 'key') else match.db_key
            help_text = match.entrytext if hasattr(match, 'entrytext') else match.db_entrytext
            # Check if object has aliases attribute
            if hasattr(match, 'aliases'):
                aliases = match.aliases if isinstance(match.aliases, list) else match.aliases.all()
            else:
                aliases = []
            suggested = []  # Don't show suggestions for exact matches
            
        # Parse for subtopics
        subtopic_map = parse_entry_for_subcategories(help_text)
        help_text = subtopic_map[None]
        subtopic_index = [subtopic for subtopic in subtopic_map if subtopic is not None]
        
        # Format and display the help entry
        topic = self.strip_cmd_prefix(topic, key_and_aliases)
        aliases = [self.strip_cmd_prefix(alias, key_and_aliases) for alias in aliases]
        
        output = self.format_help_entry(
            topic=topic,
            help_text=help_text,
            aliases=aliases,
            subtopics=subtopic_index,
            suggested=suggested,
            click_topics=self.clickable_topics
        )
        self.msg_help(output) 