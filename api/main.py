from fastapi import FastAPI
from routes.documents.router import router as document_router
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()


app.include_router(document_router)
