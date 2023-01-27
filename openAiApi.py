import openai

class ApiManager:
    def __init__(self, apiKey):
        openai.api_key = apiKey 

    def prompt(self, prompt, model="text-davinci-003", 
            temperature=0.0, nTokens=None):
        if nTokens == None:
            completionTokens = 32
        else:
            #openai doesn't seem to have a way to progamatically count tokens!
            #they use this heuristic
            estimatedPromptTokens = int(len(prompt) / 4)
            completionTokens = nTokens - estimatedPromptTokens
        response = openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=completionTokens
                )
        return response
    
    def uploadFile(self, filename):
        with open(filename, 'rb') as file:
            response = openai.File.create(
                    file=file,
                    purpose='fine-tune'
                    )
        return response
    
    def deleteFile(self, filename):
        #TODO need to be careful of this because the file may not be fully uploaded
        #by the time this function is called
        response = openai.File.delete(filename)
        return response

    def listFiles(self):
        return openai.File.list()

    def listFineTunes(self):
        return openai.FineTune.list()

    def train(self, filename, model="davinci"):
        return openai.FineTune.create(training_file=filename, model=model)

    def deleteModel(self, modelName):
        return openai.Model.delete(modelName)

    def listModels(self):
        return openai.Model.list()

        
#print(promptAi("5+5"))
#resp = uploadFile("sampleData.json")
#print(resp)
#fileId = resp['id']
#fileId = "file-Fnip6t91ISqqds1YUEhkiGLx"
#resp = openai.File.list()
#print(deleteFile(fileId))
#resp = openai.FineTune.create(training_file=fileId, model='davinci')
#resp = openai.FineTune.list()
#print(resp)
#breakpoint()

