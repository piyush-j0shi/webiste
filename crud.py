from sqlalchemy.orm import Session
from models import BlogPost, User
from typing import List, Optional
import json
from security import get_password_hash 

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: dict):
    hashed_password = get_password_hash(user['password'])
    db_user = User(username=user['username'], hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_posts(db: Session) -> List[BlogPost]:
    return db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()

def get_post_by_id(db: Session, post_id: int) -> Optional[BlogPost]:
    return db.query(BlogPost).filter(BlogPost.id == post_id).first()

def create_blog_post(
    db: Session,
    title: str,
    content: str,
    owner_id: int, 
    tags: List[str] = None
) -> BlogPost:
    if tags is None:
        tags = []

    db_post = BlogPost(
        title=title,
        content=content,
        owner_id=owner_id, 
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
    tags: List[str] = None
) -> Optional[BlogPost]:
    db_post = get_post_by_id(db, post_id)
    if not db_post:
        return None

    if title is not None:
        db_post.title = title
    if content is not None:
        db_post.content = content
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

def get_posts_by_author_username(db: Session, username: str) -> List[BlogPost]:
    return db.query(BlogPost).join(User).filter(User.username == username).order_by(BlogPost.created_at.desc()).all()
