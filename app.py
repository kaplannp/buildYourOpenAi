import os
from pathlib import Path
import json

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from openAiApi import ApiManager

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "UploadedFiles"

if not os.path.exists("UploadedFiles"):
    os.mkdir("UploadedFiles")




VALID_FILE_EXTENSIONS = {"json"}
def isValidFilename(filename):
    '''
    pulled from flask docs
    '''
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in VALID_FILE_EXTENSIONS

class Controller:

    def __init__(self, apiManager, templateGen):
        self._handlers = {}
        self._apiManager = apiManager
        self._templateGen = templateGen

    def index(self, request):
        if request.method=="GET":
            return self.handleStartup(request)
        elif request.method=="POST":
            return self.post(request)

    def handleStartup(self, request):
        resp = self._apiManager.listFiles()
        filenames = []
        for fileData in resp["data"]:
            filenames.append((fileData["id"], fileData["filename"]))
        return render_template("index.html", files=filenames)


    def post(self, request):
        for name in request.form.keys():
            if name in self._handlers:
                self._handlers[name].handle(request, self._templateGen)
                return self._templateGen.render()

    def registerHandler(self, name, handler):
        self._handlers[name] = handler

    def removeHandler(self, name):
        del self._handlers[name]

class PersistentAppData(dict):
    '''
    This class is a dictionary that stores and reads data in json format from
    the passed file. It only reads when it is instantiated, which is fine, just
    don't go messing with it's file with ANYTHING. This class handles the
    writes automatically on the set. You also can't currently have two of these
    objects with same filename, and I haven't protected you against that. If
    things get bigger you might implement generator pattern
    '''

    def __init__(self, dataFilename):
        self._filepath = os.path.join("MetaData", dataFilename)
        if not os.path.exists("MetaData"):
            os.mkdir("MetaData")
        if not os.path.exists(self._filepath):
            with(open(self._filepath, 'w')) as fid:
                fid.write("{}")
        with open(self._filepath, 'r') as json_file:
            d = json.load(json_file)
            for key, value in d.items():
                super().__setitem__(key, value)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        with open(self._filepath, 'w') as file:
            json.dump(self, file)

    def invGet(self, inKey):
        '''
        This is slow, but I don't think it needs to be fast
        '''
        out = 'nokeyfoundidentifier39440133'
        seenKey = False
        for val, key in self.items():
            if seenKey:
                assert(inKey!=key), "duplicate key in inverse"
            else:
                if inKey == key:
                    out = val
                    seenKey=True
        if not seenKey:
            raise KeyError("key not in inverse")
        return out

class TemplateRenderer:
    '''
    This class is responsible for maintaining state of all of the variables that
    are associated with the template rendering. Handlers modify the
    attributes of this class, and it takes care of rendering the template.
    The setable attributes of this class directly correspond to the attributes
    of the template.

    You might consider making this more general, it takes in a list of 
    attributes to maintain, and the name of a template. Then you make a new one
    for each template
    '''


    def render(self):
        return render_template("index.html", files=filenames)

    def __init__(self, template, attrs):
        self._TEMPLATE = template
        self._params = {attr:[] for attr in attrs}
    
    def set(self, param, val):
        self._params[param] = val

    def render(self):
        return render_template(self._TEMPLATE, **self._params)

class SubmitButtonHandler:

    def __init__(self, apiManager):
        self._responses = []
        self._prompts = []
        self._apiManager = apiManager

    def clear(self):
        self._responses = []
        self._prompts = []

    def handle(self, request, templateGen):
        prompt = request.form.get('textbox')
        model = request.form.get("model")
        response = self._apiManager.prompt(prompt, model=model)
        completion = response["choices"][0]["text"]
        self._prompts.append(prompt)
        self._responses.append(completion)
        conversation=zip(self._prompts, self._responses)
        templateGen.set("conversation", conversation)

class ClearButtonHandler:

    def __init__(self, submitButtonHandler):
        #note you need submit Button handler because you should clear it's list
        self._submitButtonHandler = submitButtonHandler

    def handle(self, request, templateGen):
        self._submitButtonHandler.clear()
        templateGen.set("conversation", [])

class FileListHandler:
    #TODO this class is starting to get large. You may wish to pull out
    # model managing from file managing from training queue.

    def __init__(self, apiManager, filenameLookup):
        self._apiManager = apiManager
        self._fileData = []
        self._fineTunes = []
        self._filenameLookup = filenameLookup

    def handle(self, request, templateGen):
        if "refresh" in request.form:
            self._refresh()
        if "upload" in request.form:
            self._upload()
        if "train" in request.form:
            self._train(request)
        if "delete" in request.form:
            self._delete(request)
        templateGen.set("files", self.getFilenames())
        templateGen.set("models", self.getModelnames())
        templateGen.set("fineTunes",self.getFineTunes())

    def getModelnames(self):
        modelnames = set()
        for fineTuneData in self._fineTunes:
            modelnames.add(fineTuneData["fine_tuned_model"])
        return modelnames

    def getFilenames(self):
        filenames = []
        for fileData in self._fileData:
            fileid = fileData["id"]
            try:
                filename = self._filenameLookup[fileid]
                filenames.append((fileid, filename))
            except KeyError:
                print(fileid)
        return filenames
    
    def getFineTunes(self):
        '''
        creates a 2d array (list of lists) where each row is:
          + finetune id
          + modelProduced
          + baseModel
          + status
        '''
        fineTunes = []
        for fineTune in self._fineTunes:
            row = []
            row.append(fineTune["id"])
            row.append(fineTune["fine_tuned_model"])
            row.append(fineTune["model"])
            row.append(fineTune["status"])
            fineTunes.append(row)
        return fineTunes

    def _refresh(self):
        resp = self._apiManager.listFiles()
        self._fileData = resp["data"]
        resp = self._apiManager.listFineTunes()
        self._fineTunes = resp["data"]

    def _delete(self, request):
        #the form.keys has other gunk too, so we compare it against filenames
        #I was nice enough to throw an error if you can't find the country
        delFile = ""
        for reqFileId in request.form.keys():
            for fileId, _ in self.getFilenames():
                if fileId == reqFileId:
                    delFile = reqFileId
                    break
        assert(delFile != "") #you did't find a file

        #I think this should be fine because if the file was on the list,
        #then it has definitely been uploaded, so you can delete it.
        self._apiManager.deleteFile(delFile)
        self._refresh()
    
    #TODO gotta refresh models automatically on startup
    def _train(self, request):
        #TODO considering making the checkbox a multiple choice
        #TODO this is untested. Difficult to make sure that the request has
        #gone through without being able to either monitor the finetunes, or
        #being able to run tests with the model

        #the form.keys has other gunk too, so we compare it against filenames
        #I was nice enough to throw an error if you can't find the country
        trainFile = ""
        for reqFileId in request.form.keys():
            for fileId, _ in self.getFilenames():
                if fileId == reqFileId:
                    trainFile = reqFileId
                    break
        assert(trainFile != "") #you did't find a file
                    
        model = request.form["model"]
        if model == "createModel":
            self._apiManager.train(trainFile) #use default
        else:
            self._apiManager.train(model, trainFile)
    
    def _upload(self):
        fileStorage = request.files["fileChooser"]
        #self._filenameLookup[filestorage.file
        assert(isValidFilename(fileStorage.filename)) #need to change for prod
        filename = secure_filename(fileStorage.filename)
        fileStorage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        resp = self._apiManager.uploadFile(filename)
        self._filenameLookup[resp['id']] = filename
        self._refresh()


with open("apiKey", 'r') as file:
    apiKey = file.read()[:-1] #drop newline
    apiManager = ApiManager(apiKey)
templateRenderer = TemplateRenderer("index.html",
        ["template", "conversation", "files", "models", "fineTunes"]
        )
controller = Controller(apiManager, templateRenderer)
submitButtonHandler = SubmitButtonHandler(apiManager)
clearButtonHandler = ClearButtonHandler(submitButtonHandler)
filenameLookup = PersistentAppData('filenames.json')
fileListHandler = FileListHandler(apiManager, filenameLookup)
controller.registerHandler("submitPrompt", submitButtonHandler)
controller.registerHandler("clear", clearButtonHandler)
controller.registerHandler("refresh", fileListHandler)
controller.registerHandler("train", fileListHandler)
controller.registerHandler("upload", fileListHandler)
controller.registerHandler("delete", fileListHandler)

@app.route("/", methods=("GET","POST"))
def main():
    return controller.index(request)

