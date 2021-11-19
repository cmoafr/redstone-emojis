from discord_slash.utils.manage_components import create_actionrow, create_select, create_select_option, ButtonStyle

class Component:

    BLUE = ButtonStyle.blue
    GRAY = ButtonStyle.gray
    GREEN = ButtonStyle.green
    RED = ButtonStyle.red

    def __init__(self, name, color, callback=None):
        self.name = name
        self.color = color
        self.callback = callback

    @staticmethod
    def generate(data):
        raise NotImplementedError
        components = []

        for row in data:
            if len(row == 1) and type(row[0]) == dict: # Is menu
                options = []
                components.append(create_actionrow(
                    create_select()
                ))

            else: # Buttons
                for component in row:
                    pass
                components.append(create_actionrow())

        return components