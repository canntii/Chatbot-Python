from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import  Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

import os
from dotenv import load_dotenv
from starlette.websockets import WebSocketDisconnect

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
chatResponse = []



openai = OpenAI(
    api_key= os.getenv('OPENAI_API_SECRET_KEY')
)

chatLog = [{'role': 'system',
            'content' : 'You are Robert Greene'
            }]


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("Home.html", {"request": request, "chatResponse": chatResponse})



@app.websocket("/ws")
async def chat(websocket:WebSocket):

    await websocket.accept()

    while True:
        userInput = await websocket.receive_text()
        chatLog.append({'role': 'user', 'content':userInput})
        chatResponse.append(userInput)

        try:
            response = openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages= chatLog,
                temperature= 0.6,
                stream=True
            )

            aiResponse = ''

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    aiResponse += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)
            chatResponse.append(aiResponse)

        except WebSocketDisconnect:
            print("Cliente desconectado")
        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request:Request, userInput:Annotated[str, Form()]):
    chatLog.append({'role':'user', 'content':userInput})
    chatResponse.append(userInput)

    response = openai.chat.completions.create(
        model= 'gpt-3.5-turbo',
        messages= chatLog,
        temperature=0.6
    )

    botResponse = response.choices[0].message.content
    chatLog.append({'role': 'assistant', 'content': botResponse})
    chatResponse.append(botResponse)

    return templates.TemplateResponse("Home.html", {"request": request, "chatResponse": chatResponse})



@app.get("/Image", response_class=HTMLResponse)
async def imagePage(request: Request):
    return templates.TemplateResponse("Image.html", {"request":request})

@app.post("/Image", response_class=HTMLResponse)
async def createImage(request:Request, userInput:Annotated[str, Form()]):
    response = openai.images.generate(
        prompt=userInput,
        n=1,
        size="256x256"
    )
    imageUrl = response.data[0].url
    return templates.TemplateResponse("Image.html", {"request":request, "imageUrl": imageUrl})

