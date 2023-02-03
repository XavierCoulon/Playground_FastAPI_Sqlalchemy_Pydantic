from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import models, schemas
from database import engine, SessionLocal
from auth import get_current_user, get_user_exception


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return bcrypt_context.hash(password)


# Category CRUD

@app.get("/categories")
async def get_categories_by_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    return db.query(models.Category).filter(models.Category.owner_id == user.get("id")).all()

@app.get("/categories/{category_id}")
def get_category(category_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).filter(models.Category.owner_id == user.get("id")).first()
    if category is not None:
        return category
    raise http_exception()

@app.post("/categories")
def create_category(category: schemas.CategoryCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    category = models.Category(name=category.name, owner_id=user.get("id"))
    db.add(category)
    db.commit()
    db.refresh(category)
    return {"status": 201, "transaction": "category created", "id": category.id }

@app.delete("/categories/{category_id}")
def delete_category(category_id: int,
                user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    
    if user is None:
        raise get_user_exception()

    category = db.query(models.Category).filter(models.Category.id == category_id).filter(models.Category.owner_id == user.get("id")).first()
    
    if category is None:
        raise http_exception()
    
    db.query(models.Category).filter(models.Category.id == category_id).delete()
    
    db.commit()
    return {"status": 200, "transaction": "category deleted" }


# Todo CRUD

@app.get("/todos")
async def get_todos_by_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    return db.query(models.Todo).options(joinedload(models.Todo.category)).filter(models.Todo.owner_id == user.get("id")).all()

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = db.query(models.Todo).options(joinedload(models.Todo.category)).filter(models.Todo.id == todo_id).filter(models.Todo.owner_id == user.get("id")).first()
    if todo is not None:
        return todo
    raise http_exception()


@app.post("/todos")
def create_todo(todo: schemas.TodoCreate,
                user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    new_todo = models.Todo(**todo.dict(), owner_id=user.get("id"))
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return {"status": 201, "new todo": new_todo }

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int,
                todo: schemas.TodoCreate,
                user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    
    if user is None:
        raise get_user_exception()

    todo_to_update = db.query(models.Todo).filter(models.Todo.id == todo_id).filter(models.Todo.owner_id == user.get("id")).first()
    
    if todo_to_update is None:
        raise http_exception()
    
    todo_to_update.title = todo.title
    todo_to_update.description = todo.description
    todo_to_update.priority = todo.priority
    todo_to_update.complete = todo.complete
    todo_to_update.category_id = todo.category_id
    
    db.add(todo_to_update)
    db.commit()
    return {"status": 200, "transaction": "todo updated" }

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int,
                user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    
    if user is None:
        raise get_user_exception()

    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).filter(models.Todo.owner_id == user.get("id")).first()
    
    if todo is None:
        raise http_exception()
    
    db.query(models.Todo).filter(models.Todo.id == todo_id).delete()
    
    db.commit()
    return {"status": 200, "transaction": "todo deleted" }

def http_exception():
    return HTTPException(status_code=404, detail="Item not found")

