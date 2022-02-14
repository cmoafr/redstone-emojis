from discord_slash.utils.manage_components import create_actionrow, create_button, create_select, create_select_option, ButtonStyle

class Component:

    BLUE = ButtonStyle.blue
    GRAY = ButtonStyle.gray
    GREEN = ButtonStyle.green
    RED = ButtonStyle.red

    def __init__(self, text=None, color=GRAY, callback=None, emoji=None, options=None, default=False):
        self.text = text or ("" if emoji != None else "\u00A0")
        self.color = color
        self.callback = callback
        self.emoji = emoji
        self.options = options
        self.default = default

    @staticmethod
    def generate(data):
        components = []

        for row in data:
            if type(row) == Component and row.options: # Menu select
                components.append(create_actionrow(
                    create_select(
                        [
                            create_select_option(
                                option.text.split("\n")[0],
                                option.callback,
                                option.emoji,
                                option.text.split("\n")[1] if "\n" in option.text else None,
                                option.default
                            )
                            for option in row.options
                        ],
                        row.callback,
                        row.default
                    )
                ))

            else: # Buttons
                comp_row = []
                for component in row:
                    comp_row.append(create_button(
                        component.color,
                        component.text,
                        component.emoji,
                        component.callback
                    ))
                components.append(create_actionrow(*comp_row))

        return components