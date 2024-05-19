from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated
import hashlib
import datetime


from openai import OpenAI

app = FastAPI()

templates = Jinja2Templates(directory="templates")


class Chat:
    def __init__(self):
        self.client = OpenAI(project='proj_81JCtsjbaUTipQ0hVmLJzCGs')
        self.prompt = {
            "role": "system",
            "content": "You're native english speaker. You'll help me to understand English texts. I will send you a text and then you will ask which part of this text I dont understand. And the you'll explain me it in given context.",
        }

        self.message_pool = {}
        # eg {"dfafafa11231": [{"role": "system", "content": "prompt"}, {"role": "user", "content": "response"}, {"role": "assistent", "content": "response"}]

    def get_message_history(self, unique_id: str):
        message_history = self.message_pool.get(unique_id, [])

        if not len(message_history):
            message_history.append(self.prompt)
            self.message_pool[unique_id] = message_history

        return message_history

    def ask_ai(self, question: str, unique_id: str):
        # todo don't like how it looks
        messages = self.get_message_history(unique_id)

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


@app.get("/explainer/{text}", response_class=HTMLResponse)
async def explain(request: Request, text: str):
    uid = generate_unique_id(text)

    message_history = client.ask_ai(text, uid)

    return templates.TemplateResponse(
        request=request, name="explainer_.html", context={"history": message_history, "client_id": uid}
    )


@app.post("/question/")
async def ask(request: Request, question: Annotated[str, Form()], client_id: Annotated[str, Form()]):
    message_history = client.ask_ai(question, client_id)

    return templates.TemplateResponse(
        request=request,
        name="explainer_.html",
        context={"history": message_history, "client_id": client_id},
    )