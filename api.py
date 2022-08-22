from typing import Union

import requests
from fastapi import FastAPI, responses

app = FastAPI()
Token = 123


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/market/cart", status_code=403)
async def cart(token: int):
    if token != Token:
        return responses.Response(status_code=400)
    else:
        return "OK"
