import openai

class ApiManager:
    def __init__(self, apiKey):
        openai.api_key = apiKey 

    def prompt(self, prompt, model="text-davinci-003"):
        #openai doesn't seem to have a way to progamatically count tokens!
        #they use this heuristic
        tokens = int(len(prompt) / 4)
        MAX_TOKENS = 4096
        BUFFER = 200
        N_TOKENS = MAX_TOKENS - tokens - BUFFER
        N_TOKENS = 32 #DEBUG This prevents from using up the budget
        response = openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=1.0,
                max_tokens=N_TOKENS
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

