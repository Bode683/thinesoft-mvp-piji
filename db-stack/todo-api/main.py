from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging
import os

from database import SessionLocal, engine
from models import Base, Todo
from schemas import TodoCreate, TodoUpdate, TodoResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Todo API",
    description="A simple todo API with CRUD operations",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint for container monitoring"""
    return {"status": "healthy", "service": "todo-api"}

@app.get("/todos", response_model=List[TodoResponse])
async def get_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all todos with pagination"""
    logger.info(f"Fetching todos with skip={skip}, limit={limit}")
    todos = db.query(Todo).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(todos)} todos")
    return todos

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo by ID"""
    logger.info(f"Fetching todo with id={todo_id}")
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        logger.warning(f"Todo with id={todo_id} not found")
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo"""
    logger.info(f"Creating new todo: {todo.title}")
    db_todo = Todo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    logger.info(f"Created todo with id={db_todo.id}")
    return db_todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    """Update an existing todo"""
    logger.info(f"Updating todo with id={todo_id}")
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        logger.warning(f"Todo with id={todo_id} not found for update")
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # Update only provided fields
    update_data = todo.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    db.commit()
    db.refresh(db_todo)
    logger.info(f"Updated todo with id={todo_id}")
    return db_todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo"""
    logger.info(f"Deleting todo with id={todo_id}")
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        logger.warning(f"Todo with id={todo_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(db_todo)
    db.commit()
    logger.info(f"Deleted todo with id={todo_id}")
    return {"message": "Todo deleted successfully"}

@app.get("/todos/search/{query}")
async def search_todos(query: str, db: Session = Depends(get_db)):
    """Search todos by title or description"""
    logger.info(f"Searching todos with query: {query}")
    todos = db.query(Todo).filter(
        Todo.title.contains(query) | Todo.description.contains(query)
    ).all()
    logger.info(f"Found {len(todos)} todos matching query")
    return todos

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
