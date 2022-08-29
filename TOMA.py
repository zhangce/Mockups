

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

import asyncio

import time

import traceback

### TOGETHER API ###

from datetime import datetime
import argparse
import pycouchdb

async def together_img(prompt, MODEL="stable_diffusion"):

    db_server_address = "http://xzyao:agway-fondly-ell-hammer-flattered-coconut@db.yao.sh:5984/"

    server = pycouchdb.Server(db_server_address)
    db = server.database("global_coordinator")

    inference_details = {
        'inputs': prompt,
        'model_name': MODEL,
        'task_type': "image_generation",
        "parameters": {
            "max_new_tokens": 64,
            "return_full_text": False,
            "do_sample": True,
            "temperature": 0.8,
            "top_p": 0.95,
            "max_time": 10.0,
            "num_return_sequences": 1,
            "use_gpu": True
    },
    'outputs': None
    }

    msg_dict = {
        'job_type_info': 'latency_inference',
        'job_state': 'job_queued',
        'time': {
            'job_queued_time': str(datetime.now()),
            'job_start_time': None,
            'job_end_time': None,
            'job_returned_time': None
        },
        'task_api': inference_details
    }
    doc = db.save(msg_dict)
    current_job_key = doc['_id']
    print("Current key:", current_job_key)

    for i in range(0, 60):

        print (i)

        doc = db.get(current_job_key)
        
        if doc['job_state'] == 'job_finished' or doc['job_state'] == 'job_returned':
            doc['job_state'] = 'job_returned'
            db.save(doc)
            return (current_job_key, doc)

        await asyncio.sleep(2)

    return (current_job_key, None)


async def together_text(prompt, max_tokens, temperature, top_p, MODEL="gpt-j-6B"):

    db_server_address = "http://xzyao:agway-fondly-ell-hammer-flattered-coconut@db.yao.sh:5984/"

    server = pycouchdb.Server(db_server_address)
    db = server.database("global_coordinator")

    inference_details = {
        'inputs': prompt,
        'model_name': MODEL,
        'task_type': "seq_generation",
        "parameters": {
            "max_new_tokens": max_tokens,
            "return_full_text": False,
            "do_sample": True,
            "temperature": temperature,
            "top_p": top_p,
            "max_time": 10.0,
            "num_return_sequences": 1,
            "use_gpu": True
    },
    'outputs': None
    }

    msg_dict = {
        'job_type_info': 'latency_inference',
        'job_state': 'job_queued',
        'time': {
            'job_queued_time': str(datetime.now()),
            'job_start_time': None,
            'job_end_time': None,
            'job_returned_time': None
        },
        'task_api': inference_details
    }
    doc = db.save(msg_dict)
    current_job_key = doc['_id']
    print("Current key:", current_job_key)

    for i in range(0, 60):

        print (i)

        doc = db.get(current_job_key)
        
        if doc['job_state'] == 'job_finished' or doc['job_state'] == 'job_returned':
            doc['job_state'] = 'job_returned'
            db.save(doc)
            return (current_job_key, doc)

        await asyncio.sleep(2)

    return (current_job_key, None)

###


def huggingface_img(prompt, MODEL="multimodalart/latentdiffusion",  API_TOKEN=""):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    API_URL = "https://hf.space/embed/" + MODEL + "/+/api/predict/"
    
    r = requests.post(url='https://hf.space/embed/multimodalart/latentdiffusion/+/api/predict/', 
        json={"data": [prompt, 50,256,256,4,15]})
    
    return r.json()["data"][0].split(",")[1]


def huggingface(prompt, max_tokens, temperature, top_p, MODEL="EleutherAI/gpt-j-6B", API_TOKEN=""):
    
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

#TOKEN = "MTAwOTg1MjA5OTE1NDE2OTg5Ng.GVdHTT.RMsPWoB9sEcQm6WhtjlKRmTxA3qOp6SJ-o7mcM"
#TOKEN = "MTAwOTg1MjA5OTE1NDE2OTg5Ng.GjxbOT.aejlnZCe6YuB-N51z6uaOjRNmNo3Z5m8DJn1yY"
TOKEN = ""

bot = discord.Bot()

### Start to Build the Bot

class TOMAModel_Feedback(Modal):

    def __init__(self) -> None:

        super().__init__(title="TOMA: Provide Feedback")

        self.add_item(
            InputText(label="Better Response", placeholder = "Response",
            style=discord.InputTextStyle.long)
        )

    async def callback(self, interaction: discord.Interaction):
        
        description = self.children[0].value

        print (description, interaction.message)

        await interaction.response.defer()


class FeedbackView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None) # timeout of the view must be set to None

    @discord.ui.button(label="Submit a Better Reponse!", custom_id="button-submit", style=discord.ButtonStyle.primary, emoji="🚀")
    async def button_callback_feedback(self, button, interaction):
        modal = TOMAModel_Feedback()
        await interaction.response.send_modal(modal)


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
    bot.add_view(FeedbackView()) # Registers a View for persistent listening
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
    prompt: discord.Option(str, description="Input your prompts or file link", 
        name="prompts_or_link"),
    mode: discord.Option(str, description="Choose your mode",
        choices=["Text Generation", "Image Geneartion", "Batch Inference"],
        default = "Text Generation"),
    model: discord.Option(str, description="Choose your model",
        choices=[
            "Text: gpt-j-6B",
            "Image: stable_diffusion"
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
                model = "gpt-j-6B"
            else:
                model = model.replace("Text: ", "")

            if max_tokens is None: max_tokens = 128
            if temperature is None: temperature = 0.8
            if top_p is None: top_p = 0.95

            print ("     query hg " + model)
            print ("      /text= ", prompt) 
            #response = huggingface(prompt, max_tokens, temperature, top_p, MODEL=model)
            (key, response) = await together_text(prompt, max_tokens, temperature, top_p, MODEL=model)
            if response is None:
                await ctx.send_followup(f"Something went wrong, please check job id={key}")
                return            
            responsetext = response["task_api"]["outputs"][0]
            print ("     /done" + responsetext + "|")
            if responsetext.strip() == "": responsetext = "<ALL SPACE STRING>"

            embed = discord.Embed(title="Text Generation Result", color=discord.Color.blurple())        
            embed.add_field(name=f"Prompts", value=f"{prompt}", inline=False)

            embed.add_field(name=f"Response", value=responsetext, inline=False)

#            embed.add_field(name=f"Feedback", value="""
#                👍 => Good Result    👎 => Bad Result     🤣 => Funny Result
#                🚫 => Not Appropriate / NSFW   😱 => Scary Result 
#            """, inline=False)

            embed.add_field(name=f"Feedback", value="""
                👍 => Good   👎 => Bad   🤣 => Funny
                🚫 => Inappropriate   😱 => Scary
            """, inline=False)

            embed.set_footer(text=f"# Generated with {model} by TOMA; (max_tokens={max_tokens}, temperature={temperature}, top_p={top_p})")

            view = FeedbackView()
            msg = await ctx.send_followup(embeds=[embed], view=view)
            #view.message = result
            #view.msg = result

            #overwrite = discord.PermissionOverwrite()
            #overwrite.add_reactions = True
            #overwrite.read_messages = True
            #await channel.set_permissions(member, overwrite=overwrite)
            #
            #await msg.channel.set_permissions(bot.user, read_messages=True, add_reactions=True)

            #permission = discord.Permissions()
            #permission.read_messages = True
            #permission.add_reactions = True
            #print (permission.read_messages)
            #print (permission.add_reactions)
            
            #if permission.read_messages and permission.add_reactions:

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
                model = "stable_diffusion"
            else:
                model = model.replace("Image: ", "")

            print ("     query hg img")
            # data = huggingface_img(prompt)
            #file = discord.File(io.BytesIO(base64.b64decode(data)), filename=hashlib.md5(data.encode()).hexdigest() + ".jpg")
            
            (key, data) = await together_img(prompt, MODEL=model)
            if data is None:
                await ctx.send_followup(f"Something went wrong, please check job id={key}")
                return       

            print(data.keys())
            files = []
            filenames = []
            for o in data["task_api"]["outputs"]:
                files.append(discord.File(io.BytesIO(
                    base64.b64decode(o.encode("ascii"))
                ), filename=hashlib.md5(o.encode()).hexdigest() + ".jpg"))
                filenames.append(hashlib.md5(o.encode()).hexdigest() + ".jpg")
            
            print ("     /done")
            
            embed = discord.Embed(title=f"Image Generation Result", color=discord.Color.blurple())        
            embed.add_field(name=f"Prompts", value=f"{prompt}", inline=False)

            embed.add_field(name=f"Feedback", value="""
                👍 => Good   👎 => Bad   🤣 => Funny
                🚫 => Inappropriate   😱 => Scary
            """, inline=False)

            embed.set_footer(text=f"# Generated with {model} by TOMA")

            view = FeedbackView()
            msg = await ctx.send_followup(embeds=[embed], view=view, files=files)

            #permission = discord.Permissions()

            #if permission.read_messages and permission.add_reactions:
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


@bot.slash_command()
async def tomato(
    ctx: discord.ApplicationContext,
    prompt: discord.Option(str, description="Input your prompts or file link", 
        name="prompts_or_link"),
    mode: discord.Option(str, description="Choose your mode",
        choices=["Text Generation", "Image Geneartion", "Batch Inference"],
        default = "Text Generation"),
    model: discord.Option(str, description="Choose your model",
        choices=[
            "Text: gpt-j-6B",
            "Image: stable_diffusion"
        ],
        default = "default"),
    max_tokens: discord.Option(int, min_value=1, max_value=1024, required=False, description="(Text Generation) max_tokens"),
    temperature: discord.Option(float, min_value=0, max_value=1, required=False, description="(Text Generation) temperature"),
    top_p: discord.Option(float, min_value=0, max_value=1, required=False, description="(Text Generation) top_p")
):
    await toma(ctx, prompt, mode, model, max_tokens, temperature, top_p)




@bot.slash_command()
async def together(
    ctx: discord.ApplicationContext,
    command: discord.Option(str, description="Get status of current resources and usage", 
        choices=["status"]),
    *,
    args = ""
):
    import requests
    from dateutil import parser

    await ctx.defer()

    try:

        x = requests.get('https://planetd.shift.ml/site_stats')

        records = {}
        for site in x.json():
            site_identifier = site["site_identifier"]
            avail_gpus = site["avail_gpus"]
            total_gpus = site["total_gpus"]
            avail_tflops = site["avail_tflops"]
            total_tflops = site["total_tflops"]
            created_at = parser.parse(site["created_at"])

            if site_identifier not in records:
                records[site_identifier] = (created_at, avail_gpus, total_gpus, avail_tflops, total_tflops)
            else:
                if created_at >= records[site_identifier][0]:
                    records[site_identifier] = (created_at, avail_gpus, total_gpus, avail_tflops, total_tflops)

        from table2ascii import table2ascii

        header = ("SITE", "Total GPUs/TFLOPS", "Avail GPUs/TFLOPS")
        body = []
        sum_total_gpus = 0
        sum_total_tflops = 0
        sum_avail_gpus = 0
        sum_avail_tflops = 0
        min_time = None
        max_time = None
        for site_identifier in records:
            (created_at, avail_gpus, total_gpus, avail_tflops, total_tflops) = records[site_identifier]
            body.append((site_identifier, f"{int(total_gpus)}/{int(total_tflops)}", f"{int(avail_gpus)}/{int(avail_tflops)}"))
            sum_total_gpus = sum_total_gpus + total_gpus
            sum_total_tflops = sum_total_tflops + total_tflops
            sum_avail_gpus = sum_avail_gpus + avail_gpus
            sum_avail_tflops = sum_avail_tflops + avail_tflops

            if min_time is None:
                min_time = created_at
                max_time = created_at

            min_time = min(min_time, created_at)
            max_time = max(max_time, created_at)

        footer = ("SUM", f"{int(sum_total_gpus)}/{int(sum_total_tflops)}", f"{int(sum_avail_gpus)}/{int(sum_avail_tflops)}")

        responds = table2ascii(
            header=header,
            body=body,
            footer=footer,
        )

        responds = f"```Research Computer\n{responds}\n\nmin_time={min_time.utcnow()} UTC\nmax_time={max_time.utcnow()} UTC\n\n{args}```"
        
        await ctx.send_followup(f"{responds}")
    
    except Exception:
        error =traceback.format_exc()
        print(error)
        await ctx.send_followup(f"sorry, something went wrong. \n\n ```{error}```")


bot.run(TOKEN)


