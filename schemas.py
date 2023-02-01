from pydantic import BaseModel

class TodoBase(BaseModel):
	title: str
	description: str | None = None
	priority: int | None = None
	complete: bool

class TodoCreate(TodoBase):
	pass

class Todo(TodoBase):
	id: int
	owner_id: int
	category_id: int

	class Config:
		orm_mode = True

class UserBase(BaseModel):
	email: str
	password: str

class UserCreate(UserBase):
	pass

class User(UserBase):
	id: int
	todos: list[Todo] = []

	class Config:
		orm_mode = True

class CategoryBase(BaseModel):
	name: str

class CategoryCreate(CategoryBase):
	pass

class Category(CategoryBase):
	id: int
	todos: list[Todo] = []

	class Config:
		orm_mode = True

