from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated

from openai import OpenAI

app = FastAPI()

templates = Jinja2Templates(directory="templates")


class Chat:
    def __init__(self):
        self.client = OpenAI(project='proj_81JCtsjbaUTipQ0hVmLJzCGs')
        self.messages = [
    {
        "role": "system",
        "content": "You're native english speakar. You'll help me to understand English texts. I will send you a text and then you will ask which part of this text I dont understand. And the you'll explain me it in given context.",
    },
]

    def ask_ai(self, question):
        self.messages.append(
            {
                "role": "user",
                "content": question,
            },
        )

        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
        )
        reply = completion.choices[0].message.content
        self.messages.append(
            {"role": "assistant", "content": reply}
        )

        return self.messages


client = Chat()


@app.get("/explainer/{text}", response_class=HTMLResponse)
async def explain(request: Request, text: str):
    message_history = client.ask_ai(text)

    return templates.TemplateResponse(
        request=request, name="explainer_.html", context={"history": message_history}
    )


@app.post("/question/")
async def ask(request: Request, question: Annotated[str, Form()]):
    message_history = client.ask_ai(question)

    return templates.TemplateResponse(
        request=request,
        name="explainer_.html",
        context={"history": message_history},
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}