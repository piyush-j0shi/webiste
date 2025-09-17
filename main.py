from fastapi import FastAPI, HTTPException, Form, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from database import get_db, create_tables
from models import BlogPost, User
import crud
import schemas
import security

app = FastAPI(title="RetroLog", description="A Vintage Blogging Platform")
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except security.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = crud.get_user_by_username(db, username=username)
        return user
    except security.JWTError:
        return None

@app.on_event("startup")
def startup_event():
    create_tables()

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user_optional)):
    posts = crud.get_all_posts(db)
    posts_dict = [post.to_dict() for post in posts]
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts_dict, "current_user": current_user})

@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = crud.get_user_by_username(db, username=username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    crud.create_user(db, {"username": username, "password": password})
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=username)
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def get_post(request: Request, post_id: int, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user_optional)):
    post = crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = crud.get_comments_by_post_id(db, post_id)
    
    post_dict = post.to_dict()
    return templates.TemplateResponse(
        "post.html", 
        {
            "request": request, 
            "post": post_dict, 
            "comments": comments, 
            "current_user": current_user
        }
    )
@app.get("/new", response_class=HTMLResponse)
async def new_post_form(request: Request):
    return templates.TemplateResponse("new_post.html", {"request": request})

@app.post("/create")
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    crud.create_blog_post(
        db=db,
        title=title,
        content=content,
        owner_id=current_user.id, 
        tags=tag_list
    )
    return RedirectResponse(url="/", status_code=303)

@app.get("/post/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    return templates.TemplateResponse("edit_post.html", {"request": request, "post": post})

@app.post("/post/{post_id}/edit")
async def edit_post(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = crud.get_post_by_id(db, post_id)
    if not post or post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")
    
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    crud.update_blog_post(db, post_id=post_id, title=title, content=content, tags=tag_list)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@app.post("/post/{post_id}/delete")
async def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = crud.get_post_by_id(db, post_id)
    if not post or post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not permitted")
    
    crud.delete_blog_post(db, post_id=post_id)
    return RedirectResponse(url="/", status_code=303)

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.post("/post/{post_id}/comment")
async def post_comment(
    post_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crud.create_comment(db=db, content=content, post_id=post_id, owner_id=current_user.id)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@app.post("/comment/{comment_id}/delete")
async def delete_comment(
    comment_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    post_id = comment.post_id
    crud.delete_comment(db, comment_id=comment_id)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@app.get("/comment/{comment_id}/edit", response_class=HTMLResponse)
async def edit_comment_form(
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    return templates.TemplateResponse("edit_comment.html", {"request": request, "comment": comment})


@app.post("/comment/{comment_id}/edit")
async def edit_comment(
    comment_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    crud.update_comment(db, comment_id=comment_id, content=content)
    return RedirectResponse(url=f"/post/{comment.post_id}", status_code=303)
