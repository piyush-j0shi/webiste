from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BlogPostBase(BaseModel):
    title: str
    content: str
    author: str
    tags: List[str] = []

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

class BlogPostResponse(BlogPostBase):
    id: int
    created_at: str
    
    class Config:
        from_attributes = True

class BlogPostList(BaseModel):
    posts: List[BlogPostResponse]
    total: int
