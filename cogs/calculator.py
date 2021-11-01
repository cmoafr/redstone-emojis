import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, SlashCommandOptionType as OptionType
import re

def setup(bot):
    bot.add_cog(Calculator(bot))

class Calculator(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot



    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog calculator ready!")

    @cog_ext.cog_slash(
        name="calc",
        description="Calculate something for you",
        options=[create_option(name="calculation",
                description="What you want to be calculated",
                option_type=OptionType.STRING,
                required=True)]
    )
    async def calc(self, ctx, calculation):
        try:
            result = _calculate(_shunting_yard(_parse(calculation)))
            msg = "`" + calculation.strip() + "`\n= " + str(result)
        except Exception as e:
            msg = type(e).__name__ + ": " + str(e)
        await ctx.send(msg)





"""
class _Operation:

    list = []
    
    def __init__(self, symbol, calculation, precedance, right_associative=False):
        self.symbol = symbol
        self.calculation = calculation
        self.precedance = precedance
        self.right_assotiative = right_assiciative
        _Operation.append(self)

    def find(symbol):
        for op in _Operation.list:
            if op.symbol == symbol:
                return op
        return None



_Operation('+', lambda a, b: a + b, 4)
_Operation('-', lambda a, b: a - b, 4)
_Operation('*', lambda a, b: a * b, 3)
_Operation('/', lambda a, b: a / b, 3)
_Operation('%', lambda a, b: a % b, 3)
_Operation('^', lambda a, b: a ** b, 2, True)
"""



def _parse(expression, ignore=" \t\n"):
    parsed = []

    def to_float(expression, negative):
        if len(expression) == 0:
            raise ValueError("Expected number, found {} at position {}".format(c, i))
        try:
            num = float(expression)
        except ValueError:
            raise ValueError("{} is not a valid number at position {}".format(expression, i - len(expression)))
        if negative:
            num *= -1
        return num

    expresssion = expression.replace(' ', '')
    negative = False
    current = ""
    for i, c in enumerate(expression):
        if c in ignore:
            continue
        if c == '-' and len(current) == 0:
            negative = True
        elif c in "0123456789.":
            current += c
        elif c in "+-*/%^)":
            if len(parsed) == 0 or parsed[-1] != ')':
                num = to_float(current, negative)
                parsed.append(num)
            parsed.append(c)
            current = ""
            negative = False
        elif c in "(":
            parsed.append(c)
        else:
            raise ValueError("{} is not a valid character at position {}".format(c, i))
    if len(current) != 0:
        num = to_float(current, negative)
        parsed.append(num)
    return parsed



def _shunting_yard(parsed):

    def check_operator(operator):
        if len(stack) == 0 or stack[-1] == '(':
            return False
        precedances = {
            '+': 4,
            '-': 4,
            '*': 3,
            '/': 3,
            '%': 3,
            '^': 2,
            '(': 1,
            ')': 1
            }
        p1 = precedances[operator]
        p2 = precedances[stack[-1]]
        right_associativity = operator in '^'
        return p1 > p2 or (p1 == p2 and not right_associativity)
        """
        if stack[-1] in "()": # To be verified
            return True
        if operator in "()": # To be verified
            return False
        p1 = operator.precedance
        p2 = stack[-1].precedance
        return p1 > p2 or (p1 == p2 and not operation.right_associative)
        """

    output = []
    stack = []
    for i, token in enumerate(parsed):
        if type(token) in (int, float):
            output.append(token)
        elif token in "+-*/%^":
            while check_operator(token):
                output.append(stack.pop())
            stack.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            try:
                while stack[-1] != '(':
                    output.append(stack.pop())
            except IndexError:
                raise IndexError("Parenthesis mismatch at index {}".format(i))
            stack.pop()
            if False: # ??? "if there is a function token at the top of the operator stack"
                output.append(stack.pop())
        else:
            raise ValueError("Invalid token {} at position {}".format(token, i))
    while len(stack) != 0:
        if stack[-1] in "()":
            raise ValueError("Parenthesis mismatch (late)")
        output.append(stack.pop())
    return output



def _calculate(RPN):
    stack = []
    for token in RPN:
        if type(token) in (int, float):
            stack.append(token)
        elif type(token) == chr or type(token) == str and len(token) == 1:
            try:
                b = stack.pop()
                a = stack.pop()
            except IndexError:
                raise IndexError("RPN: Not enough numbers to calculate")
            c = None
            if token == '+': c = a + b
            if token == '-': c = a - b
            if token == '*': c = a * b
            if token == '/': c = a / b
            if token == '%': c = a % b
            if token == '^': c = a ** b
            if token == None:
                raise ValueError("RPN: Unknown operation {}".format(c))
            stack.append(c)
        else:
            raise ValueError("RPN: Unknown token: {}".format(token))
    if len(stack) != 1:
        raise ValueError("RPN: Incorrect amount of number remaining on the stack: {}".format(len(stack)))
    return stack[0]