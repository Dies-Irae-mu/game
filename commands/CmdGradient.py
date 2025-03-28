from evennia import Command
# Extensive Color Map
COLOR_MAP = {
    # General, commonly used colors
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "gray": (128, 128, 128),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "lime": (0, 255, 0),
    "maroon": (128, 0, 0),
    "navy": (0, 0, 128),
    "olive": (128, 128, 0),
    "teal": (0, 128, 128),
    "silver": (192, 192, 192),
    "gold": (255, 215, 0),
    "violet": (238, 130, 238),
    "indigo": (75, 0, 130),
    "turquoise": (64, 224, 208),
    "tan": (210, 180, 140),
    "sky": (135, 206, 235),
    "coral": (255, 127, 80),
    "salmon": (250, 128, 114),
    "plum": (221, 160, 221),
    "khaki": (240, 230, 140),
    "crimson": (220, 20, 60),

    # Basic colors (some redundant, but kept for completeness)
    "black": (0, 0, 0), "white": (255, 255, 255),
    "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
    "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),

    # Shades of gray
    "lightgray": (192, 192, 192), "darkgray": (64, 64, 64),
    "dimgray": (105, 105, 105), "slategray": (112, 128, 144),

    # Reds
    "darkred": (139, 0, 0), "firebrick": (178, 34, 34), "indianred": (205, 92, 92),
    "lightcoral": (240, 128, 128), "darksalmon": (233, 150, 122),
    "lightsalmon": (255, 160, 122), "tomato": (255, 99, 71),

    # Pinks
    "lightpink": (255, 182, 193), "hotpink": (255, 105, 180),
    "deeppink": (255, 20, 147), "palevioletred": (219, 112, 147), "mediumvioletred": (199, 21, 133),

    # Oranges
    "darkorange": (255, 140, 0), "peach": (255, 218, 185), "papayawhip": (255, 239, 213),

    # Browns
    "saddlebrown": (139, 69, 19), "sienna": (160, 82, 45),
    "chocolate": (210, 105, 30), "peru": (205, 133, 63), "sandybrown": (244, 164, 96),
    "rosybrown": (188, 143, 143), "goldenrod": (218, 165, 32), "darkgoldenrod": (184, 134, 11),

    # Yellows
    "lightyellow": (255, 255, 224), "lemonchiffon": (255, 250, 205),
    "lightgoldenrodyellow": (250, 250, 210), "palegoldenrod": (238, 232, 170),
    "darkkhaki": (189, 183, 107),

    # Greens
    "darkgreen": (0, 100, 0), "forestgreen": (34, 139, 34), "seagreen": (46, 139, 87),
    "mediumseagreen": (60, 179, 113), "limegreen": (50, 205, 50),
    "lightgreen": (144, 238, 144), "palegreen": (152, 251, 152), "springgreen": (0, 255, 127),
    "mediumspringgreen": (0, 250, 154), "darkolivegreen": (85, 107, 47),
    "olivedrab": (107, 142, 35), "lawngreen": (124, 252, 0), "chartreuse": (127, 255, 0),
    "greenyellow": (173, 255, 47),

    # Cyans
    "darkcyan": (0, 139, 139), "lightseagreen": (32, 178, 170),
    "cadetblue": (95, 158, 160), "darkturquoise": (0, 206, 209), "mediumturquoise": (72, 209, 204),
    "aqua": (0, 255, 255), "aquamarine": (127, 255, 212),
    "paleturquoise": (175, 238, 238), "lightcyan": (224, 255, 255),

    # Blues
    "darkblue": (0, 0, 139), "mediumblue": (0, 0, 205),
    "royalblue": (65, 105, 225), "steelblue": (70, 130, 180), "dodgerblue": (30, 144, 255),
    "deepskyblue": (0, 191, 255), "cornflowerblue": (100, 149, 237), "skyblue": (135, 206, 235),
    "lightskyblue": (135, 206, 250), "lightblue": (173, 216, 230), "powderblue": (176, 224, 230),

    # Purples
    "darkmagenta": (139, 0, 139),
    "darkviolet": (148, 0, 211), "darkorchid": (153, 50, 204), "mediumorchid": (186, 85, 211),
    "orchid": (218, 112, 214), "thistle": (216, 191, 216), "lavender": (230, 230, 250),
    "mediumslateblue": (123, 104, 238),
    "mediumpurple": (147, 112, 219), "blueviolet": (138, 43, 226), "slateblue": (106, 90, 205),

    # Special colors
    "aliceblue": (240, 248, 255), "ghostwhite": (248, 248, 255), "snow": (255, 250, 250),
    "seashell": (255, 245, 238), "floralwhite": (255, 250, 240), "whitesmoke": (245, 245, 245),
    "beige": (245, 245, 220), "oldlace": (253, 245, 230), "ivory": (255, 255, 240),
    "honeydew": (240, 255, 240), "mintcream": (245, 255, 250), "azure": (240, 255, 255),
}

from evennia import Command
from evennia import search_object
import re

class CmdGradientName(Command):
    """
    Apply a gradient color to your name or another player's name

    Usage:
      gradientname [<player>=]<start_color> <end_color>
      gradientname colorlist

    This command applies a gradient color effect to your name or another player's name,
    transitioning from the start color to the end color.
    You can use named colors or hex color codes (#RRGGBB).

    If you're an admin or higher, you can set the gradient for other players
    by specifying their name before the '=' sign.

    Examples:
      gradientname crimson gold
      gradientname #FF0000 #0000FF
      gradientname PlayerName=red #00FF00
      gradientname colorlist
    """

    key = "gradientname"
    # Builder+ only
    locks = "cmd:perm(Builder)"
    help_category = "Admin Commands"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: gradientname [<player>=]<start_color> <end_color>")
            self.caller.msg("       gradientname colorlist")
            return

        if self.args.lower().strip() == "colorlist":
            self.list_colors()
            return

        if "=" in self.args:
            target_name, color_args = self.args.split("=", 1)
            target_name = target_name.strip()
            if not self.caller.check_permstring("Admin"):
                self.caller.msg("You don't have permission to set gradients for other players.")
                return
            targets = search_object(target_name)
            if not targets:
                self.caller.msg(f"Could not find player '{target_name}'.")
                return
            if len(targets) > 1:
                self.caller.msg(f"Multiple matches found for '{target_name}'. Please be more specific.")
                return
            target = targets[0]
        else:
            color_args = self.args
            target = self.caller


        try:
            start_color, end_color = color_args.split()[:2]
        except ValueError:
            self.caller.msg("Please provide both start and end colors.")
            return

        
        start_rgb = self.parse_color(start_color)
        end_rgb = self.parse_color(end_color)

        if start_rgb is None or end_rgb is None:
            self.caller.msg("Invalid color(s). Use named colors or hex codes (#RRGGBB).")
            return

        gradient_name = self.create_gradient(target.key, start_rgb, end_rgb)
        
        target.db.gradient_name = gradient_name
        if target == self.caller:
            self.caller.msg(f"Your name now appears as: {gradient_name}")
        else:
            self.caller.msg(f"{target.key}'s name now appears as: {gradient_name}")
            target.msg(f"Your name has been set to appear as: {gradient_name}")

    def parse_color(self, color):
        if color.startswith('#'):
            # Parse hex color code
            match = re.match(r'^#([0-9A-Fa-f]{6})$', color)
            if match:
                hex_color = match.group(1)
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif color.lower() in COLOR_MAP:
            # Use named color
            return COLOR_MAP[color.lower()]
        return None

    def create_gradient(self, text, start_rgb, end_rgb):
        gradient = []
        for i, char in enumerate(text):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / (len(text) - 1))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / (len(text) - 1))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / (len(text) - 1))
            
            ansi_code = self.rgb_to_ansi(r, g, b)
            gradient.append(f"\033[38;5;{ansi_code}m{char}\033[0m")

        return "".join(gradient)

    def rgb_to_ansi(self, r, g, b):
        # Convert RGB to the closest ANSI 256 color code
        return 16 + (36 * (r // 51)) + (6 * (g // 51)) + (b // 51)

    def list_colors(self):
        color_list = sorted(COLOR_MAP.keys())
        columns = 4
        rows = -(-len(color_list) // columns)  # Ceiling division
        
        table = []
        for i in range(rows):
            row = color_list[i::rows]
            table.append("  ".join(word.ljust(20) for word in row))
        
        self.caller.msg("Available colors:\n" + "\n".join(table))