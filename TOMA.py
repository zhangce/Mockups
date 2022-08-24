

from asyncore import file_dispatcher
from random import choices
from socket import MsgFlag
import discord
from discord import option

from discord.ui import InputText, Modal, Select, Button, Item

import os
import json
import requests
import io
import base64
import hashlib

import traceback

def huggingface_img(prompt, MODEL="multimodalart/latentdiffusion",  API_TOKEN="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"):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    API_URL = "https://hf.space/embed/" + MODEL + "/+/api/predict/"
    
    r = requests.post(url='https://hf.space/embed/multimodalart/latentdiffusion/+/api/predict/', 
        json={"data": [prompt, 50,256,256,4,15]})
    
    return r.json()["data"][0].split(",")[1]


def huggingface(prompt, max_tokens, temperature, top_p, MODEL="EleutherAI/gpt-j-6B", API_TOKEN="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"):
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    API_URL = "https://api-inference.huggingface.co/models/" + MODEL
    def query(payload):
        data = json.dumps(payload)
        response = requests.request("POST", API_URL, headers=headers, data=data)
        return json.loads(response.content.decode("utf-8"))
    data = query({
        "inputs": prompt, "parameters": {
            "max_new_tokens": max_tokens, "return_full_text": False,
            "do_sample": True, "temperature": temperature, "top_p": top_p,
            "max_time": 100.0, "num_return_sequences": 1,
        }
    })
    return data[0]["generated_text"]

TOKEN = "MTAwOTg1MjA5OTE1NDE2OTg5Ng.GVdHTT.RMsPWoB9sEcQm6WhtjlKRmTxA3qOp6SJ-o7mcM"

bot = discord.Bot()

### Start to Build the Bot

"""
class FeedbackView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View


    def __init__(self):
        super().__init__(timeout=None) # timeout of the view must be set to None

    @discord.ui.button(label="Good", custom_id="button-Good", style=discord.ButtonStyle.primary, emoji="👍")
    async def button_callback_good(self, button, interaction):
        #import pdb
        #pdb.set_trace()

        print(interaction.message)

        await interaction.message.add_reaction('👍')
        await interaction.response.defer()


    @discord.ui.button(label="Funny", custom_id="button-Funny", style=discord.ButtonStyle.primary, emoji="👍") 
    async def button_callback_funny(self, button, interaction):
        print(interaction.message)
        await interaction.message.add_reaction('👍')
        await interaction.response.defer()

    @discord.ui.button(label="Bad", custom_id="button-Bad", style=discord.ButtonStyle.danger, emoji="👎") 
    async def button_callback_bad(self, button, interaction):
        print(interaction.message)
        await interaction.message.add_reaction('👎')
        await interaction.response.defer()

    @discord.ui.button(label="NSFW", custom_id="button-NSFW", style=discord.ButtonStyle.danger, emoji="👎") 
    async def button_callback_nsfw(self, button, interaction):
        print(interaction.message)
        await interaction.message.add_reaction('👎')
        await interaction.response.defer()

    @discord.ui.button(label="Too Dark", custom_id="button-TooDark", style=discord.ButtonStyle.danger, emoji="👎") 
    async def button_callback_dark(self, button, interaction):
        print(interaction.message)
        await interaction.message.add_reaction('👎')
        await interaction.response.defer()
"""

@bot.event
async def on_ready():
    #bot.add_view(FeedbackView()) # Registers a View for persistent listening
    return

class TOMAModel_Batch(Modal):

    def __init__(self, filelink) -> None:

        self.filelink = filelink

        super().__init__(title="TOMA: Batch Inference Mode")

        self.add_item(
            InputText(label="Description of Your Project", placeholder = "Description",
            style=discord.InputTextStyle.long)
        )

        self.add_item(
            InputText(label="Input File", value=self.filelink)
        )


        #self.add_item(
        #    Select(options=[discord.SelectOption(label="1"), discord.SelectOption(label="2")])
        #)

    async def callback(self, interaction: discord.Interaction):
        
        description = self.children[0].value
        filename = self.children[1].value

        embed = discord.Embed(title="Batch Inference Task Created", color=discord.Color.blurple())
        
        embed.add_field(name="User: ", value=interaction.user.id, inline=False)
        embed.add_field(name="Task: ", value=filename, inline=False)
        embed.add_field(name="Project: ", value=description, inline=False)

        await interaction.response.send_message(embeds=[embed])

@bot.slash_command()
async def toma(
    ctx: discord.ApplicationContext,
    mode: discord.Option(str, description="Choose your mode", 
        choices=["Text Generation", "Image Geneartion", "Batch Inference"]),
    prompt: discord.Option(str, description="Input your prompts or file link", 
        name="prompts_or_link"),
    model: discord.Option(str, description="Choose your model",
        choices=[
            "Text: EleutherAI/gpt-neo-125M",
            "Text: EleutherAI/gpt-neo-1.3B",
            "Text: EleutherAI/gpt-neo-2.7B",
            "Text: EleutherAI/gpt-j-6B",
            "Text: EleutherAI/gpt-neox-20b",
            "Image: multimodalart/latentdiffusion"
        ],
        default = "default"),
    max_tokens: discord.Option(int, min_value=1, max_value=1024, required=False, description="(Text Generation) max_tokens"),
    temperature: discord.Option(float, min_value=0, max_value=1, required=False, description="(Text Generation) temperature"),
    top_p: discord.Option(float, min_value=0, max_value=1, required=False, description="(Text Generation) top_p")
):

    print (f"{mode}; {model}; {prompt};")

    if mode == "Text Generation":

        await ctx.defer()

        try:
            if model == "default": 
                model = "EleutherAI/gpt-j-6B"
            else:
                model = model.replace("Text: ", "")

            if max_tokens is None: max_tokens = 128
            if temperature is None: temperature = 0.8
            if top_p is None: top_p = 0.95

            print ("     query hg" + model)
            print ("      /text= ", prompt) 
            response = huggingface(prompt, max_tokens, temperature, top_p, MODEL=model)
            print ("     /done")

            embed = discord.Embed(title="Text Generation Result", color=discord.Color.blurple())        
            embed.add_field(name=f"Prompts: \"{prompt}\"", value=response, inline=False)

            embed.add_field(name=f"Feedback", value="""
                👍 => Good Result    👎 => Bad Result     🤣 => Funny Result
                🚫 => Not Appropriate / NSFW   😱 => Scary Result 
            """, inline=False)

            embed.set_footer(text=f"# Generated with {model} by TOMA; (max_tokens={max_tokens}, temperature={temperature}, top_p={top_p})")

            #view = FeedbackView()
            msg = await ctx.send_followup(embeds=[embed])   #, view=view)
            #view.message = result
            #view.msg = result

            await msg.add_reaction('👍')
            await msg.add_reaction('👎')
            await msg.add_reaction('🤣')
            await msg.add_reaction('🚫')
            await msg.add_reaction('😱')

        except Exception:
            error =traceback.format_exc()
            print(error)
            await ctx.send_followup(f"sorry, something went wrong. \n\n ```{error}```")

    elif mode == "Image Geneartion":

        await ctx.defer()

        try:
            if model == "default":
                model = "multimodalart/latentdiffusion"
            else:
                model = model.replace("Image: ", "")

            print ("     query hg img")
            data = huggingface_img(prompt)
            file = discord.File(io.BytesIO(base64.b64decode(data)), filename=hashlib.md5(data.encode()).hexdigest() + ".jpg")
            print ("     /done")
            
            embed = discord.Embed(title=f"Image Generation Result", color=discord.Color.blurple())        
            embed.add_field(name=f"Prompts: \"{prompt}\"", value=file.filename, inline=False)

            embed.add_field(name=f"Feedback", value="""
                👍 => Good Result    👎 => Bad Result     🤣 => Funny Result
                🚫 => Not Appropriate / NSFW   😱 => Scary Result 
            """, inline=False)

            embed.set_footer(text=f"# Generated with {model} by TOMA")

            msg = await ctx.send_followup(embeds=[embed], file=file)

            await msg.add_reaction('👍')
            await msg.add_reaction('👎')
            await msg.add_reaction('🤣')
            await msg.add_reaction('🚫')
            await msg.add_reaction('😱')

        except Exception:
            error =traceback.format_exc()
            print(error)
            await ctx.send_followup(f"sorry, something went wrong. \n\n ```{error}```")

    elif mode == "Batch Inference":

        try:
            modal = TOMAModel_Batch(prompt)

            await ctx.interaction.response.send_modal(modal)
        except Exception:
            error =traceback.format_exc()
            print(error)
            await ctx.send_followup(f"sorry, something went wrong. \n\n ```{error}```")

    else:
        await ctx.respond(f"Unknown mode: {mode}", view=FeedbackView())


bot.run(TOKEN)


