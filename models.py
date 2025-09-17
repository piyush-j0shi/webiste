from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime
import json

Base = declarative_base()

class BlogPost(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(Text, default="[]")  # Store as JSON string
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": json.loads(self.tags) if self.tags else []
        }
    
    @property
    def tags_list(self):
        return json.loads(self.tags) if self.tags else []
    
    @tags_list.setter
    def tags_list(self, value):
        self.tags = json.dumps(value)
