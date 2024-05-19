import os
from fastapi import FastAPI, Form, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated
import hashlib
import datetime


from openai import OpenAI

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")


class Chat:
    def __init__(self):
        self.client = OpenAI(project='proj_81JCtsjbaUTipQ0hVmLJzCGs')
        self.message_pool = {}
        # eg: {
        # "dfafafa11231": [
        #     {"role": "system", "content": "prompt"},
        #     {"role": "user", "content": "response"},
        #     {"role": "assistent", "content": "response"},
        # ]

    def get_message_history(self, unique_id: str, prompt=None):
        message_history = self.message_pool.get(unique_id, [])

        if not len(message_history):
            message_history.append(
                {
                    "role": "system",
                    "content": prompt,
                }
            )
            self.message_pool[unique_id] = message_history

        return message_history

    def ask_ai(self, question: str, unique_id: str, prompt=None):
        # todo don't like how it looks
        messages = self.get_message_history(unique_id, prompt)

        messages.append(
            {
                "role": "user",
                "content": question,
            },
        )

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        reply = completion.choices[0].message.content
        messages.append(
            {"role": "assistant", "content": reply}
        )

        return messages


client = Chat()


def generate_unique_id(input_string: str) -> str:
    current_time = datetime.datetime.now().isoformat()
    data_to_hash = input_string + current_time
    hash_object = hashlib.sha256(data_to_hash.encode())
    unique_id = hash_object.hexdigest()
    return unique_id


@app.get("/explainer/{token}/{text}", response_class=HTMLResponse)
async def explain(request: Request, token: str, text: str):
    if os.environ['SECURE'] != token:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    prompt = "You're native english speaker. You'll help me to understand English texts. I will send you a text and then you will ask which part of this text I dont understand. And the you'll explain me it in given context."


    uid = generate_unique_id(text)

    message_history = client.ask_ai(text, uid, prompt)

    return templates.TemplateResponse(
        request=request, name="explainer.html", context={"history": message_history, "client_id": uid, "token": token}
    )


@app.get("/explainer_rs/{token}/{text}", response_class=HTMLResponse)
async def explain(request: Request, token: str, text: str):
    if os.environ['SECURE'] != token:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    prompt = "You're native serbian speaker. You'll help me to understand Serbian texts. I will send you a text and then you will ask which part of this text I dont understand. And the you'll explain me in english it in given context."

    uid = generate_unique_id(text)

    message_history = client.ask_ai(text, uid, prompt)

    return templates.TemplateResponse(
        request=request, name="explainer.html", context={"history": message_history, "client_id": uid, "token": token}
    )


@app.post("/question/")
async def ask(
        request: Request,
        question: Annotated[str, Form()],
        client_id: Annotated[str, Form()],
        token: Annotated[str, Form()],
):
    if os.environ['SECURE'] != token:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    message_history = client.ask_ai(question, client_id)

    return templates.TemplateResponse(
        request=request,
        name="explainer.html",
        context={"history": message_history, "client_id": client_id, "token": token},
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}