from sqlalchemy import INTEGER, FLOAT, BIGINT, VARCHAR, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from api.database_setup import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(30), unique=True, index=True)
    email: Mapped[str] = mapped_column(VARCHAR(40), unique=True)
    password: Mapped[str] = mapped_column(VARCHAR())
    projects: Mapped[list["Project"]] = relationship(back_populates="user", cascade='all,delete')



class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(40), index=True)
    vulnerability_score: Mapped[float] = mapped_column(FLOAT)
    efficiency_score: Mapped[float] = mapped_column(FLOAT)
    coverage_score: Mapped[float] = mapped_column(FLOAT)
    reliability_score: Mapped[float] = mapped_column(FLOAT)
    standarisation_score: Mapped[float] = mapped_column(FLOAT)
    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("user.id"))
    # Define the many-to-one relationship with User
    user: Mapped["User"] = relationship(back_populates="projects")


class Company(Base):
    __tablename__ = "company"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(40), unique=True ,index=True) ## -> czy na pewno musi byc unique?
    # job_offers: Mapped[list["JobOffer"]] = relationship(back_populates="company", cascade='all,delete')
    employers: Mapped[list["Employer"]] = relationship(back_populates="company", cascade='all,delete')
    # company = relationship("Employer", back_populates="company")


class Employer(Base):
    __tablename__ = "employer"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(30), unique=True, index=True)
    email: Mapped[str] = mapped_column(VARCHAR(40))
    password: Mapped[str] = mapped_column(VARCHAR(255))
    company_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("company.id"))
    company: Mapped["Company"] = relationship(back_populates="employers")
    job_offers: Mapped[list["JobOffer"]] = relationship(back_populates="employer", cascade='all,delete')


class JobOffer(Base):
    __tablename__ = "job_offer"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    position: Mapped[str] = mapped_column(VARCHAR(40))
    job_description: Mapped[str] = mapped_column(VARCHAR())
    required_skills: Mapped[str] = mapped_column(VARCHAR())
    salary: Mapped[int] = mapped_column(INTEGER)
    employer_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("employer.id"))
    employer: Mapped["Employer"] = relationship(back_populates="job_offers")
    # company = relationship("Company", back_populates="job_offer")
