
from celery_app.utils import create_celery
from tasks.task_1 import task_1
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from mangum import Mangum


# from getting_user_repos import GetUserRepos

# Replace 'sqlite:///./test.db' with your desired database connection string.
DATABASE_URL = "sqlite:///./test.db"

# FastAPI instance
app = FastAPI()

# SQLAlchemy configuration
handler = Mangum(app)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app.celery_app = create_celery()
celery = app.celery_app


# SQLAlchemy Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    projects = relationship("Project", back_populates="user", cascade='all,delete')


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    vulnerability_score = Column(Float)
    efficiency_score = Column(Float)
    coverage_score = Column(Float)
    reliability_score = Column(Float)
    standarisation_score = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    # Define the many-to-one relationship with User
    user = relationship("User", back_populates="projects")


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True ,index=True) ## -> czy na pewno musi byc unique?
    job_offers = relationship("JobOffer", back_populates="company", cascade='all,delete')


class JobOffer(Base):
    id = Column(Integer, primary_key=True, index=True)
    position = Column(String)
    job_description = Column(String)
    required_skills = Column(String)
    salary = Column(Integer)
    company_id = Column(Integer, ForeignKey("company.id"))
    company = relationship("Company", back_populates="job_offer")


# Pydantic Model for User (response)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str


# Pydantic Model for User (request - create/update)
class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    vulnerability_score: float
    efficiency_score: float
    coverage_score: float
    reliability_score: float
    standarisation_score: float
    user_id: int


# Pydantic Model for Project (request - create/update)


class ProjectCreate(BaseModel):
    name: str
    vulnerability_score: float
    efficiency_score: float
    coverage_score: float
    reliability_score: float
    standarisation_score: float
    user_id: int


class CompanyCreate(BaseModel):
    id: int
    name: str


class CompanyResponse(BaseModel):
    id: int
    name: str


class JobOfferCreate(BaseModel):
    id: int
    position: str
    required_skills: str
    position: str
    salary: int
    job_description: str
    company_id: int



# class TaskOut(BaseModel):
#     id: str
#     status: str


Base.metadata.create_all(bind=engine)


@app.get("/start/{access_token}")
def start(username, password, email, access_token):
    user = User(username=username, password=password, email=email)
    db = SessionLocal()
    db.add(user)
    print(user.id)
    db.commit()
    db.refresh(user)
    db.close()
    kwargs = {"access_token": access_token}
    projects = task_1.apply_async(queue="user_github_que2", kwargs=kwargs)
    for name, ratings in projects.get().items():
        project = Project(name=name, vulnerability_score=ratings["vulnerability_score"],
                          efficiency_score=ratings["efficiency_score"], coverage_score=ratings["coverage_score"],
                          reliability_score=ratings["reliability_score"],
                          standarisation_score=ratings["standarisation_score"], user_id=db.query(User).filter(User.username==username).first().id)
        db = SessionLocal()
        db.add(project)
        db.commit()
        db.refresh(project)
        db.close()


# Routes
@app.post("/users/", response_model=UserResponse)
def create_user(user_data: UserCreate):
    user = User(username=user_data.username, password=user_data.password)
    # Add the user to the database
    db = SessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return UserResponse(id=user.id, username=user.username)


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    # Retrieve a user by ID
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=user.id, username=user.username)


@app.get("/users")
def get_all_users():
    db = SessionLocal()
    users = db.query(User).all()
    print(users)
    db.close()

    if not users:
        raise HTTPException(status_code=404, detail="Users not found")

    return users


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserCreate):
    # Update a user by ID
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    user.username = user_data.username
    user.password = user_data.password
    user.scores = user_data.scores
    db.commit()
    db.refresh(user)
    db.close()

    return UserResponse(id=user.id, username=user.username)


@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int):
    # Delete a user by ID
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    db.close()

    return UserResponse(id=user.id, username=user.username)


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    db = SessionLocal()
    project = db.query(Project).filter(Project.id == project_id).first()
    db.close()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/projects")
def get_all_projects_of_user(user_id):
    db = SessionLocal()
    project = db.query(Project).filter(Project.user_id == user_id).all()
    print(project)
    db.close()
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project


@app.get("/all_projects")
def get_all_projects():
    db = SessionLocal()
    project = db.query(Project).all()
    print(project)
    db.close()
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project


@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_data: ProjectCreate):
    db = SessionLocal()
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in project_data.dict().items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    db.close()
    return project


@app.delete("/projects/{project_id}", response_model=ProjectResponse)
def delete_project(project_id: int):
    db = SessionLocal()
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    db.close()
    return project
