import discord
from discord import app_commands
from discord.ext import commands

import traceback
from typing import Tuple

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Brainfuck(bot))



async def message_error(e: Exception, interaction: discord.Interaction) -> None:
    error = str(e)
    # tb = traceback.format_exc()
    # message = f"Error: `{error}` ```{tb}```"
    message = f"Error: `{error}`"
    await interaction.response.send_message(message)

class Program:
    TIMEOUT = 2**20
    OVERFLOW = 30_000
    MAX_LOOPS = 256
    
    def __init__(self, code: str) -> None:
        self.code: str = code
        self.index: int = 0
        self.memory: list[int] = [0]
        self.address: int = 0
        self.loops: list[int] = []
        self.output: str = ""
        self.check()

    def run(self, input: str = "") -> Tuple[str, bool]:
        self.check(input)
        
        runtime = 0
        while self.index < len(self.code):
            match self.code[self.index]:

                case '+':
                    self.set((self.get()+1)%256)
                case '-':
                    self.set((self.get()-1)%256)
                case '>':
                    self.address += 1
                    if self.address == len(self.memory):
                        self.memory.append(0)
                case '<':
                    self.address -= 1
                    if self.address < 0:
                        self.memory.insert(0, 0)
                        for i, pos in enumerate(self.loops):
                            self.loops[i] = pos + 1
                case '[':
                    if self.get():
                        self.loops.append(self.index)
                    else:
                        count = 0
                        while True:
                            self.index += 1
                            if self.code[self.index] == '[':
                                count += 1
                            elif self.code[self.index] == ']':
                                if count == 0:
                                    break
                                count -= 1
                case ']':
                    self.index = self.loops.pop() - 1
                case '.':
                    #print(chr(self.get()), end='')
                    self.output += chr(self.get())
                case ',':
                    if not input:
                        return self.output, True
                    c, input = input[0], input[1:]
                    self.set(ord(c))

            self.index += 1

            runtime += 1
            if runtime > Program.TIMEOUT:
                raise TimeoutError("Program took too long to repond")
            if len(self.memory) > Program.OVERFLOW:
                raise MemoryError("Memory too large")
            if len(self.loops) > Program.MAX_LOOPS:
                raise RecursionError("Too many nested loops")

        return self.output, False

    def get(self) -> int:
        return self.memory[self.address]

    def set(self, value: int) -> None:
        if value < 0 or value > 255:
            raise ValueError(f"Invalid value {value}")
        self.memory[self.address] = value

    def check(self, input: str = "") -> None:
        count = 0
        for i, c in enumerate(self.code):
            if c == '[':
                count += 1
            elif c == ']':
                count -= 1
            if count < 0:
                raise SyntaxError("Extra ']' found at position "+str(i))
        if count != 0:
            raise SyntaxError("Missing ']'")
        if not input.isascii():
            raise ValueError("Invalid input contains non-ASCII characters")
    
    async def interact(self, interaction: discord.Interaction, input: str = ""):
        try:
            output, need_input = self.run(input)
            if need_input:
                await interaction.response.send_modal(Input(self, output))
            else:
                if output:
                    output = "```" + output + "```"
                else:
                    output = "No output"
                await interaction.response.send_message("Result: "+output)
        except Exception as e:
            await message_error(e, interaction)



class Input(discord.ui.Modal, title="Input"):
    output = discord.ui.TextInput(
        label="Output",
        placeholder="Your previous code returned no output",
        required=False
    )
    input_ = discord.ui.TextInput(
        label="Input",
        required=True
    )

    value: str = ""

    def __init__(self, program: Program, output: str = "") -> None:
        super().__init__()
        self.program: Program = program
        if output:
            self.output.placeholder = output

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.callback(interaction)
    
    async def callback(self, interaction: discord.Interaction) -> None:
        input = self.input_.value
        self.program.interact(interaction, input)

class Brainfuck(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.logger.info("Cog brainfuck ready!")


    @app_commands.command(name="brainfuck", description="Run a Brainfuck program")
    @app_commands.describe(code="Brainfuck code to be executed")
    async def brainfuck(self, interaction: discord.Interaction, code: str) -> None:
        # await interaction.response.send_message("Running...")
        try:
            program = Program(code)
        except Exception as e:
            await message_error(e, interaction)
            return

        await program.interact(interaction)
