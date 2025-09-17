from sqlalchemy.orm import Session
from models import BlogPost, User, Comment
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

def create_comment(db: Session, content: str, post_id: int, owner_id: int):
    db_comment = Comment(content=content, post_id=post_id, owner_id=owner_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_post_id(db: Session, post_id: int) -> List[Comment]:
    return db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc()).all()

def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
    return db.query(Comment).filter(Comment.id == comment_id).first()

def delete_comment(db: Session, comment_id: int):
    db_comment = get_comment_by_id(db, comment_id)
    if db_comment:
        db.delete(db_comment)
        db.commit()
        return True
    return False

def update_comment(db: Session, comment_id: int, content: str) -> Optional[Comment]:
    db_comment = get_comment_by_id(db, comment_id)
    if db_comment:
        db_comment.content = content
        db.commit()
        db.refresh(db_comment)
        return db_comment
    return None
