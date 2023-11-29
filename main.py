from celery_app.utils import create_celery
from tasks.task_1 import task_1
from fastapi import Depends
from fastapi import FastAPI, HTTPException
import time
from pydantic import BaseModel
from mangum import Mangum
from auth.JWT_handler import sign_jwt
from auth.JWT_bearer import JwtBearer
from api.database_setup import Base, engine, get_db
from api.models.models import User, JobOffer, Project, Company
from passlib.context import CryptContext
from celery.result import AsyncResult
import asyncio
from fastapi import Body
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Annotated

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


class UserLogin(BaseModel):
    name: str
    password: str

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    name: str | None = None

#will create table into database
Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(user_password):
    return pwd_context.hash(user_password)


def verify_password(plain_text_password, hashed_password):
    return pwd_context.verify(plain_text_password, hashed_password)

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return {"user": user, "is_employer": f'{user.employer_flag}'}

@app.get("/get_user/me/", tags=['all'])
async def get_user_me(
    token, db = Depends(get_db)
):
    return await get_current_user(token, db)

@app.post("/login_for_token", response_model=Token, tags=['all'])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db=Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/start/{access_token}", tags=['developer'])
async def start(username, password, email, access_token=None, db=Depends(get_db)):
    if access_token is None:
        return "give access token"
    password = get_hashed_password(password)
    user = User(username=username, password=password, email=email)
    db.add(user)
    print(user.id)
    db.commit()
    db.refresh(user)
    kwargs = {"access_token": access_token, "folder": "/home/ubuntu/tests/testtt"}
    result = task_1.apply_async(queue="user_github_que2", kwargs={"access_token": access_token, "folder": "/home/ubuntu/tests/testtt"})
    async def wait_for_result(result):
        while not result.ready():
            await asyncio.sleep(1)
        return result.get(timeout=1)

    if result.ready():
        projects = result.get(timeout=1)
    else:
        projects = await wait_for_result(result)
    for name, ratings in projects.items():
        project = Project(name=name, vulnerability_score=ratings["vulnerability_score"],
                          efficiency_score=ratings["efficiency_score"], coverage_score=ratings["coverage_score"],
                          reliability_score=ratings["reliability_score"],
                          standarisation_score=ratings["standarisation_score"], user_id=db.query(User).filter(User.username==username).first().id,
                          employer_flag=False)
        db.add(project)
        db.commit()
        db.refresh(project)
    return {"user_id": user.id}


@app.get("/get_employer/{user_id}", tags=['developer'], dependencies=[Depends(JwtBearer())])
def get_employer(user_id: int, db=Depends(get_db)):
    # Retrieve a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/get_developer/{user_id}", tags=['employer'], dependencies=[Depends(JwtBearer())])
def get_developer(user_id: int, db=Depends(get_db)):
    # Retrieve a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/get_all_users", tags=['tester_func'])
def get_all_users(db=Depends(get_db)):
    users = db.query(User).all()
    print(users)

    if not users:
        raise HTTPException(status_code=404, detail="Users not found")

    return users


@app.put("/update_user/{user_id}", tags=['admin'], response_model=UserResponse)
def update_user(user_id: int, username: str, password: str, db=Depends(get_db)):
    # Update a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = username
    user.password = get_hashed_password(password)
    db.commit()
    db.refresh(user)

    return {"message": "succesfully altered user"}


@app.put("/update_user/me", tags=['all'], response_model=UserResponse)
async def update_user_me(token: str, username: str, password: str, db=Depends(get_db)):
    # Update a user by ID
    user = await get_current_user(token, db)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = username
    user.password = get_hashed_password(password)
    db.commit()
    db.refresh(user)

    return {"message": "succesfully altered user"}


@app.delete("/delete_user/{user_id}", tags=['admin'])
def delete_user(user_id: int, db=Depends(get_db)):
    # Delete a user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return f"deleted user: {user}"

@app.delete("/delete_user/me", tags=['all'])
async def delete_user_me(token: str, db=Depends(get_db)):
    # Delete a user by ID
    user = await get_current_user(token, db)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return f"deleted user: {user}"

@app.get("/get_project/{project_id}", tags=['all'], response_model=ProjectResponse)
def get_project(project_id: int, db=Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/get_all_projects_of_user/{user_id}", tags=['all'])
def get_all_projects_of_user(user_id, db=Depends(get_db)):
    project = db.query(Project).filter(Project.user_id == user_id).all()
    print(project)
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project

@app.get("/get_all_projects_of_user/me", tags=['all'])
async def get_all_projects_of_user_me(token, db=Depends(get_db)):
    user = await get_current_user(token, db)
    project = db.query(Project).filter(Project.user_id == user.id).all()
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project

@app.get("/all_projects", tags=['tester_func'])
def get_all_projects(db=Depends(get_db)):
    project = db.query(Project).all()
    if not project:
        raise HTTPException(status_code=404, detail="Projects not found")
    return project


@app.delete("/delete_project/{project_id}", tags=['admin'])
def delete_project(project_id: int, db=Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": f"successfully deleted project with id: {project_id}"}

@app.delete("/delete_project/me/{project_id}", tags=['developer'])
async def delete_project_me(token, project_id: int, db=Depends(get_db)):
    user = await get_current_user(token, db)
    projects = db.query(Project).filter(Projects.user_id == user.id).all()
    project = projects.filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": f"successfully deleted project with id: {project_id}"}


@app.post("/add_job_offer/me/{job_offer_id}", tags=['employer'], response_model=JobOfferCreate)
async def add_job_offer_me(token: str, position: str, required_skills: str, salary: int, job_description: str,
                  company_name: str, db=Depends(get_db)):
    user = await get_current_user(token, db)
    if user.employer_flag is False:
        return {"error_message": "you are not employer"}
    job_offer = JobOffer(position=position, required_skills=required_skills, salary=salary,
                         job_description=job_description, employer_id=user.id)
    db.add(job_offer)
    db.commit()
    db.refresh(job_offer)
    return JobOfferCreate(id=job_offer.id, position=position, required_skills=required_skills, salary=salary,
                         job_description=job_description, employer_id=user_id)

@app.post("/add_job_offer_temp_user/me/{job_offer_id}", tags=['employer'], response_model=JobOfferCreate)
async def add_job_offer_temp_user_me(token: str, position: str, required_skills: str, salary: int, job_description: str,
                  company_name: str, db=Depends(get_db)):
    user = await get_current_user(token, db)
    if user.employer_flag is False:
        return {"error_message": "you are not employer"}
    job_offer = JobOffer(position=position, required_skills=required_skills, salary=salary,
                         job_description=job_description, employer_id=user.id)
    db.add(job_offer)
    db.commit()
    db.refresh(job_offer)
    return JobOfferCreate(id=job_offer.id, position=position, required_skills=required_skills, salary=salary,
                         job_description=job_description, employer_id=user_id)

@app.get("/job_offers/{company_id}")
def get_offers_from_company(company_name, db=Depends(get_db), tags=['tester_func']):
    all_offers = []
    employers = db.query(Company).filter(Company.name == company_name).first().user
    for employer in employers:
        job_offers = db.query(JobOffer).filter(JobOffer.employer_id == employer.id).all()
        all_offers = all_offers.extend(job_offers)
    return all_offers


@app.post("/create_employer_account", tags=['employer'])
def create_employer_account(username: str, email: str, password: str, db=Depends(get_db)):
    employer = User(username=username, email=email, password=get_hashed_password(password), employer_flag=True)
    db.add(employer)
    db.commit()
    db.refresh(employer)
    return {"message": "succesfully added employer", "employer_id": employer.id}


@app.post("/get_employers", tags=['tester_func'])
def get_employers(db=Depends(get_db)):
    employers = db.query(Employer).all()
    if not employers:
        raise HTTPException(status_code=404, detail="no employers")

    return {"employers": employers}


@app.post("/get_companies", tags=['tester_func'])
def get_companies(db=Depends(get_db)):
    companies  = db.query(Company).all()
    if not companies:
        raise HTTPException(status_code=404, detail="no companies")

    return {"companies": companies}
