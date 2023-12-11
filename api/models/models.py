from sqlalchemy import INTEGER, FLOAT, BIGINT, VARCHAR, Column, ForeignKey, ARRAY, String, BOOLEAN
from sqlalchemy.orm import relationship, Mapped, mapped_column
from api.database_setup import Base


class Company(Base):
    __tablename__ = "company"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(40), unique=True ,index=True) ## -> czy na pewno musi byc unique?
    user: Mapped[list["User"]] = relationship(back_populates="company", cascade='all,delete')


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(30), unique=True, index=True)
    email: Mapped[str] = mapped_column(VARCHAR(40), unique=True)
    password: Mapped[str] = mapped_column(VARCHAR())
    projects: Mapped[list["Project"]] = relationship(back_populates="user", cascade='all,delete')
    company_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("company.id"), nullable=True)
    company: Mapped["Company"] = relationship(back_populates="user")
    job_offers: Mapped[list["JobOffer"]] = relationship(back_populates="employer", cascade='all,delete')
    employer_flag: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(40), index=True)
    vulnerability_score: Mapped[float] = mapped_column(FLOAT)
    efficiency_score: Mapped[float] = mapped_column(FLOAT)
    coverage_score: Mapped[float] = mapped_column(FLOAT)
    reliability_score: Mapped[float] = mapped_column(FLOAT)
    standarisation_score: Mapped[float] = mapped_column(FLOAT)
    type: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    language: Mapped[str] = mapped_column(VARCHAR(), nullable=True)
    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("user.id"))
    # Define the many-to-one relationship with User
    user: Mapped["User"] = relationship(back_populates="projects")


class JobOffer(Base):
    __tablename__ = "job_offer"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    position: Mapped[str] = mapped_column(VARCHAR(40))
    job_description: Mapped[str] = mapped_column(VARCHAR())
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String))
    salary: Mapped[int] = mapped_column(INTEGER)
    employer_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("user.id"))
    employer: Mapped["User"] = relationship(back_populates="job_offers")
