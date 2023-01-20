import os

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

    def __init__(self, apiManager):
        self._handlers = {}
        self._apiManager = apiManager

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
                return self._handlers[name].handle(request)

    def registerHandler(self, name, handler):
        self._handlers[name] = handler

    def removeHandler(self, name):
        del self._handlers[name]

class SubmitButtonHandler:

    def __init__(self, apiManager):
        self._responses = []
        self._prompts = []
        self._apiManager = apiManager

    def clear(self):
        self._responses = []
        self._prompts = []

    def handle(self, request):
        prompt = request.form.get('textbox')
        response = self._apiManager.promptAi(prompt)
        completion = response["choices"][0]["text"]
        self._prompts.append(prompt)
        self._responses.append(completion)
        conversation=zip(self._prompts, self._responses)
        return render_template("index.html", conversation=conversation)

class ClearButtonHandler:

    def __init__(self, submitButtonHandler):
        #note you need submit Button handler because you should clear it's list
        self._submitButtonHandler = submitButtonHandler

    def handle(self, request):
        self._submitButtonHandler.clear()
        return render_template("index.html", responses=[])

class FileListHandler:
    def __init__(self, apiManager):
        self._apiManager = apiManager
        self._fileData = []

    def handle(self, request):
        if "refresh" in request.form:
            self._refresh()
        if "upload" in request.form:
            self._upload()
        if "train" in request.form:
            self._train()
        return render_template("index.html", files=self.getFilenames())

    def getFilenames(self):
        filenames = []
        for fileData in self._fileData:
            filenames.append((fileData["id"], fileData["filename"]))
        return filenames

    def _refresh(self):
        resp = self._apiManager.listFiles()
        self._fileData = resp["data"]
    
    def _train(self):
        pass
    
    def _upload(self):
        fileStorage = request.files["fileChooser"]
        assert(isValidFilename(fileStorage.filename)) #need to change for prod
        filename = secure_filename(fileStorage.filename)
        fileStorage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        resp = self._apiManager.uploadFile(filename)
        self._refresh()


with open("apiKey", 'r') as file:
    apiKey = file.read()[:-1] #drop newline
    apiManager = ApiManager(apiKey)
controller = Controller(apiManager)
submitButtonHandler = SubmitButtonHandler(apiManager)
clearButtonHandler = ClearButtonHandler(submitButtonHandler)
fileListHandler = FileListHandler(apiManager)
controller.registerHandler("submitPrompt", submitButtonHandler)
controller.registerHandler("clear", clearButtonHandler)
controller.registerHandler("refresh", fileListHandler)
controller.registerHandler("train", fileListHandler)
controller.registerHandler("upload", fileListHandler)

@app.route("/", methods=("GET","POST"))
def main():
    return controller.index(request)

