from sqlalchemy.orm import Session
from models import BlogPost
from typing import List, Optional
import json

def get_all_posts(db: Session) -> List[BlogPost]:
    return db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()

def get_post_by_id(db: Session, post_id: int) -> Optional[BlogPost]:
    return db.query(BlogPost).filter(BlogPost.id == post_id).first()

def create_blog_post(
    db: Session, 
    title: str, 
    content: str, 
    author: str, 
    tags: List[str] = None
) -> BlogPost:
    if tags is None:
        tags = []
    
    db_post = BlogPost(
        title=title,
        content=content,
        author=author,
        tags=json.dumps(tags)
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

def update_blog_post(
    db: Session, 
    post_id: int, 
    title: str = None, 
    content: str = None, 
    author: str = None, 
    tags: List[str] = None
) -> Optional[BlogPost]:
    db_post = get_post_by_id(db, post_id)
    
    if not db_post:
        return None
    
    if title is not None:
        db_post.title = title
    if content is not None:
        db_post.content = content
    if author is not None:
        db_post.author = author
    if tags is not None:
        db_post.tags = json.dumps(tags)
    
    db.commit()
    db.refresh(db_post)
    
    return db_post

def delete_blog_post(db: Session, post_id: int) -> bool:
    db_post = get_post_by_id(db, post_id)
    
    if not db_post:
        return False
    
    db.delete(db_post)
    db.commit()
    
    return True

def search_posts(db: Session, query: str) -> List[BlogPost]:
    return db.query(BlogPost).filter(
        BlogPost.title.contains(query) | 
        BlogPost.content.contains(query)
    ).order_by(BlogPost.created_at.desc()).all()

def get_posts_by_author(db: Session, author: str) -> List[BlogPost]:
    return db.query(BlogPost).filter(
        BlogPost.author == author
    ).order_by(BlogPost.created_at.desc()).all()
