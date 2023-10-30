from celery_app.utils import create_celery
from tasks.task_1 import task_1
from fastapi import Depends
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum
from api.database_setup import Base, engine, get_db
from api.models.models import User, JobOffer, Employer, Project, Company
from passlib.context import CryptContext

# FastAPI instance
app = FastAPI()

handler = Mangum(app)
app.celery_app = create_celery()
celery = app.celery_app


# Pydantic Model for User (response)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str


# Pydantic Model for User (request - create/update)
class UserCreate(BaseModel):
    id: int
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
    salary: int
    job_description: str
    company_id: int


#will create table into database
Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(user_password):
    return pwd_context.hash(user_password)


def verify_password(plain_text_password, hashed_password):
    return pwd_context.verify(plain_text_password, hashed_password)


@app.post("/start/{access_token}")
def start(username, password, email, access_token=None, db=Depends(get_db)):
    if access_token is None:
        pass
        return "employer_account_created"
    user = User(username=username, password=password, email=email)
    db.add(user)
    print(user.id)
    db.commit()
    db.refresh(user)
    kwargs = {"access_token": access_token, "folder": "/home/ubuntu/tests/testtt"}
    projects = task_1.apply_async(queue="user_github_que2", kwargs=kwargs)
    for name, ratings in projects.get().items():
        project = Project(name=name, vulnerability_score=ratings["vulnerability_score"],
                          efficiency_score=ratings["efficiency_score"], coverage_score=ratings["coverage_score"],
                          reliability_score=ratings["reliability_score"],
                          standarisation_score=ratings["standarisation_score"], user_id=db.query(User).filter(User.username==username).first().id)
        db.add(project)
        db.commit()
        db.refresh(project)


# Routes
@app.post("/users/", response_model=UserResponse)
def create_user(username:str, email:str, password:str, db=Depends(get_db)):
    password = get_hashed_password(password)
    user = User(username=username, password=password, email=email)
    # Add the user to the database
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(id=user.id, username=user.username, email=email)


@app.get("/login")
def login(username:str, password:str, db=Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    return verify_password(password, user.password)


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db=Depends(get_db)):
    # Retrieve a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=user.id, username=user.username)


@app.get("/users")
def get_all_users(db=Depends(get_db)):
    users = db.query(User).all()
    print(users)

    if not users:
        raise HTTPException(status_code=404, detail="Users not found")

    return users


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserCreate, db=Depends(get_db)):
    # Update a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = user_data.username
    user.password = user_data.password
    user.scores = user_data.scores
    db.commit()
    db.refresh(user)

    return UserResponse(id=user.id, username=user.username)


@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db=Depends(get_db)):
    # Delete a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return UserResponse(id=user.id, username=user.username)


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db=Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/projects")
def get_all_projects_of_user(user_id, db=Depends(get_db)):
    project = db.query(Project).filter(Project.user_id == user_id).all()
    print(project)
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project


@app.get("/all_projects")
def get_all_projects(db=Depends(get_db)):
    project = db.query(Project).all()
    print(project)
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project


@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_data: ProjectCreate, db=Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in project_data.dict().items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@app.delete("/projects/{project_id}", response_model=ProjectResponse)
def delete_project(project_id: int, db=Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return project


@app.post("/job_offer/{job_offer_id}", response_model=JobOfferCreate)
def add_job_offer(position: str, required_skills: str, salary: int, job_description: str,
                  company_name: str, db=Depends(get_db)):
    try:
        db.query(Company).filter(Company.name == company_name).first().id
    except AttributeError:
        company = Company(name=company_name)
        db.add(company)
        db.commit()
        db.refresh(company)
    company_id = db.query(Company).filter(Company.name == company_name).first().id
    job_offer = JobOffer(position=position, required_skills=required_skills, salary=salary,
                         job_description=job_description, company_id=company_id)
    db.add(job_offer)
    db.commit()
    db.refresh(job_offer)
    return JobOfferCreate(id=job_offer.id, position=position, required_skills=required_skills, salary=salary,
                         job_description=job_description, company_id=company_id)


@app.get("/job_offers")
def get_offers(company_name, db=Depends(get_db)):
    company_id = db.query(Company).filter(Company.name == company_name).first().id
    job_offers = db.query(JobOffer).filter(JobOffer.company_id == company_id).all()
    return job_offers
