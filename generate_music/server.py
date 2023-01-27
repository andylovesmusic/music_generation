import numpy as np
from collections.abc import Iterable
import numpy as np
import openai
import music21
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from midi2audio import FluidSynth
from typing import Union
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "*",
    "https://andylovesmusic.github.io/",
    "http://localhost",
    "http://localhost:3000",
]

openai.api_key = "" # OpenAI API Key
fs = FluidSynth()
song_cnt = 0

def write_song(abc_song):
  global song_cnt
  songn = 'sample{}'.format(song_cnt)
  with open("generated/{}.abc".format(songn), "w") as new_song_file:
    new_song_file.write(abc_song)

  song = music21.converter.parse("generated/{}.abc".format(songn))
  song.write('xml', fp='generated/{}.xml'.format(songn))
  xml = music21.converter.parse('generated/{}.xml'.format(songn))
  xml.write('midi', "generated/{}.midi".format(songn))
  song_cnt += 1
  fs.midi_to_audio(f'generated/{songn}.midi', f'generated/{songn}.wav')
  return f'generated/{songn}.wav'

def gen_title(text):
  text = text.replace("\"", "")
  prompt = "generate music title based on the following text.\n" + text + "\nTitle:"
  response = openai.Completion.create(
    model="text-davinci-003",
    prompt=prompt,
    temperature=0.5,
    top_p=1.0,
    frequency_penalty=0,
    presence_penalty=0,
    max_tokens = 50)
  title = response["choices"][0]["text"].strip()
  print(title)
  title = title.replace("\"", "")
  return title

def gen_music(title):
  band_name = "Andy and Lewis"
  song_name = title
  prompt = "X: 1 $ T: " + song_name + " $ C: " + band_name + " $ <song>"
  response = openai.Completion.create(
    #model="curie:ft-personal-2022-11-16-03-25-21",
    #model="davinci:ft-personal-2023-01-24-06-01-08",
    model="curie:ft-personal-2023-01-24-06-37-32",
    prompt=prompt,
    stop = " |$ <end>",
    temperature=0.5,
    top_p=1.0,
    frequency_penalty=0,
    presence_penalty=0,
    max_tokens = 1000)
  
  band_name = "Andy"

  formatted_prompt = "X: 1 $ T: " + title + " $ C: " + band_name + " $ L: 1/4 $ Q: 1/4=150 $ M: 4/4 $ K: C $ V: 1 treble"
  formatted_prompt = formatted_prompt.replace(" $ ", "\n")
  formatted_prompt = formatted_prompt.replace("<song>", "").strip()
  
  formatted_song = response["choices"][0]["text"].strip()
  formatted_song = formatted_song.replace('`', '"')
  formatted_song = formatted_song.replace(" $ ", "\n")
  new_song = formatted_prompt+ "\n" + formatted_song
  return write_song(new_song)

#gen_title("happy")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/piano")
async def piano(text: Union[str, None] = None):
  if text:
    try:
      return {"ok": True, "songn": gen_music(gen_title(text))}
    except(e):
      print(e)
      return {"ok": False, "msg": "internal error, try again later"}
  return {"ok": False, "msg": "empty text"}
  
app.mount("/generated", StaticFiles(directory="generated"), name="generated")

  