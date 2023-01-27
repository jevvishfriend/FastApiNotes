import json
import math
import typing
from typing import List

import requests
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

import models
from database import engine
from database import get_db
from models import Note, NotePydantic, NoteOut

middleware = [
    Middleware(SessionMiddleware, secret_key='secretkey')
]
app = FastAPI(middleware=middleware, debug=True)
templates = Jinja2Templates(directory="templates")
models.Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


def flash(request: Request, message: typing.Any, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
        request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    print(request.session)
    return request.session.pop("_messages") if "_messages" in request.session else []


templates.env.globals['get_flashed_messages'] = get_flashed_messages


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    context = {'request': request}
    return templates.TemplateResponse("base.html", context)


@app.get("/catfacts", response_class=HTMLResponse)
async def catfacts(request: Request):
    res = requests.get('https://cat-fact.herokuapp.com/facts/random')
    if res.status_code != requests.codes.ok:
        data = {"text": "COS POSZŁO NIE TAK I NIE BYŁO MNIE SŁYCHAC"}
    else:
        data = json.loads(res.content)
    context = {'request': request, 'data': data['text']}
    return templates.TemplateResponse("catfacts.html", context)


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    context = {'request': request, }
    return templates.TemplateResponse("login.html", context)


@app.get("/notes", response_class=HTMLResponse)
async def notes(request: Request):
    db = get_db()
    all_notes = db.query(Note).all()
    context = {'request': request, "all_notes": all_notes}
    return templates.TemplateResponse("notes.html", context)


# deleting note from frontend
@app.post("/delete-note/", response_class=HTMLResponse)
async def del_notes(request: Request):
    note = await request.json()
    note_id = note['noteId']
    db = get_db()
    note_to_delete = db.query(Note).get(note_id)
    if not note_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No note with this id: {note_id} found')
    db.delete(note_to_delete)
    db.commit()
    db.close()
    flash(request, "Note deleted", "success")
    context = {'request': request}
    return templates.TemplateResponse("notes.html", context)


# adding note from frontend
@app.post("/notes")
async def notes(request: Request, note: str = Form(...)):
    db = get_db()
    new_note = Note(data=note)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    all_notes = db.query(Note).all()
    db.close()
    flash(request, "Note added", "success")
    context = {'request': request, 'note': note, "all_notes": all_notes}
    return templates.TemplateResponse("notes.html", context)


# sqrt
@app.get("/sqrt")
def form_sqrt(request: Request):
    result = "Type a number"
    return templates.TemplateResponse('sqrt.html', context={'request': request, 'result': result})


# sqrt
@app.post("/add_note/")
def form_sqrt(request: Request, num: int = Form(...)):
    result = math.sqrt(num)
    return templates.TemplateResponse('sqrt.html', context={'request': request, 'result': result})


# creating a note
@app.post("/api/notes/", response_model=NotePydantic)
async def api_create_note(note: NotePydantic):
    db = get_db()
    new_note = Note(data=note.data)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    db.close()
    return new_note


#  fetching all notes
@app.get("/api/get_all_notes/", response_model=List[NoteOut])
async def read_notes():
    db = get_db()
    notes = db.query(Note).all()
    return [NoteOut(id=note.id, data=note.data, date=note.date) for note in notes]


# note by id
@app.get("/api/get_note/{noteId}")
async def read_note(id: int):
    db = get_db()
    note_query = db.query(Note).filter(Note.id == id)
    note = note_query.first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No note with this id: {id} found')
    return [NoteOut(id=note.id, data=note.data, date=note.date)]


#  deleting a note
@app.delete("/api/delete_note/{noteId}")
async def delete_note(id: int):
    db = get_db()
    note_query = db.query(Note).filter(Note.id == id)
    note = note_query.first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No note with this id: {id} found')
    note_query.delete(synchronize_session=False)
    db.commit()
    return HTTPException(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == '__main__':
    uvicorn.run('main:app', port=8000, reload=True)
