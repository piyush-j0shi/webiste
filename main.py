from fastapi import FastAPI, HTTPException, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

# Import our modules
from database import get_db, create_tables
from models import BlogPost
import crud
import schemas

# Initialize FastAPI app
app = FastAPI(title="RetroLog", description="A Vintage Blogging Platform")

# Templates
templates = Jinja2Templates(directory="templates")

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

# HTML Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    posts = crud.get_all_posts(db)
    posts_dict = [post.to_dict() for post in posts]
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "posts": posts_dict
    })

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def get_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_dict = post.to_dict()
    return templates.TemplateResponse("post.html", {
        "request": request, 
        "post": post_dict
    })

@app.get("/new", response_class=HTMLResponse)
async def new_post_form(request: Request):
    return templates.TemplateResponse("new_post.html", {"request": request})

@app.post("/create")
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    # Process tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Create post
    crud.create_blog_post(
        db=db,
        title=title,
        content=content,
        author=author,
        tags=tag_list
    )
    
    return RedirectResponse(url="/", status_code=303)

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/author/{author_name}", response_class=HTMLResponse)
async def author_posts(request: Request, author_name: str, db: Session = Depends(get_db)):
    posts = crud.get_posts_by_author(db, author_name)
    posts_dict = [post.to_dict() for post in posts]
    return templates.TemplateResponse("author.html", {
        "request": request,
        "posts": posts_dict,
        "author": author_name
    })

# API Routes
@app.get("/api/posts", response_model=List[schemas.BlogPostResponse])
async def get_all_posts_api(db: Session = Depends(get_db)):
    posts = crud.get_all_posts(db)
    return [schemas.BlogPostResponse(**post.to_dict()) for post in posts]

@app.get("/api/posts/{post_id}", response_model=schemas.BlogPostResponse)
async def get_post_api(post_id: int, db: Session = Depends(get_db)):
    post = crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return schemas.BlogPostResponse(**post.to_dict())

@app.post("/api/posts", response_model=schemas.BlogPostResponse)
async def create_post_api(post: schemas.BlogPostCreate, db: Session = Depends(get_db)):
    db_post = crud.create_blog_post(
        db=db,
        title=post.title,
        content=post.content,
        author=post.author,
        tags=post.tags
    )
    return schemas.BlogPostResponse(**db_post.to_dict())

@app.put("/api/posts/{post_id}", response_model=schemas.BlogPostResponse)
async def update_post_api(
    post_id: int, 
    post: schemas.BlogPostUpdate, 
    db: Session = Depends(get_db)
):
    db_post = crud.update_blog_post(
        db=db,
        post_id=post_id,
        title=post.title,
        content=post.content,
        author=post.author,
        tags=post.tags
    )
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return schemas.BlogPostResponse(**db_post.to_dict())

@app.delete("/api/posts/{post_id}")
async def delete_post_api(post_id: int, db: Session = Depends(get_db)):
    success = crud.delete_blog_post(db, post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}

@app.get("/api/search", response_model=List[schemas.BlogPostResponse])
async def search_posts_api(q: str, db: Session = Depends(get_db)):
    posts = crud.search_posts(db, q)
    return [schemas.BlogPostResponse(**post.to_dict()) for post in posts]

@app.get("/api/author/{author_name}", response_model=List[schemas.BlogPostResponse])
async def get_author_posts_api(author_name: str, db: Session = Depends(get_db)):
    posts = crud.get_posts_by_author(db, author_name)
    return [schemas.BlogPostResponse(**post.to_dict()) for post in posts]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
