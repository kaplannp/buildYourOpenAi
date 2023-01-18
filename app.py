import os

import openai
from flask import Flask, redirect, render_template, request, url_for
#haven't used flask so far

app = Flask(__name__)
with open("apiKey", 'r') as file:
    openai.api_key = file.read()[:-1] #drop newline

def promptAi(prompt):
    response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=1.0
            )
    return response

def uploadFile(filename):
    with open(filename, 'rb') as file:
        response = openai.File.create(
                file=file,
                purpose='fine-tune'
                )
    return response

def deleteFile(filename):
    #TODO need to be careful of this because the file may not be fully uploaded
    #by the time this function is called
    response = openai.File.delete(filename)
    return response
        
#print(promptAi("5+5"))
#resp = uploadFile("sampleData.json")
#print(resp)
#fileId = resp['id']
fileId = "file-Fnip6t91ISqqds1YUEhkiGLx"
#resp = openai.File.list()
#print(deleteFile(fileId))
#resp = openai.FineTune.create(training_file=fileId, model='davinci')
resp = openai.FineTune.list()
print(resp)
breakpoint()

