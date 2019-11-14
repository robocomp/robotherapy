from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Sequence, ForeignKey, Text
from sqlalchemy.orm import relationship

Base = declarative_base()


class Patient(Base):
    __tablename__ = 'patient'
    id = Column(Integer, Sequence('patient_id_seq'))
    username = Column(String(20), primary_key=True)
    nombre = Column(String(60))
    sexo = Column(String(20))
    edad = Column(Integer)
    datosRegistro = Column(Text())
    nivelCognitivo = Column(Integer)
    nivelFisico = Column(Integer)
    nivelJuego = Column(Integer)
    centro = Column(Integer)
    profesional = Column(String(20))
    observaciones = Column(Text())
    fechaAlta = Column(String(20))

    session = relationship("Session", back_populates="patient", cascade="all, delete")

    def __repr__(self):
        return "<Patient(username='%s' nombre=%s')>" % (self.username, self.nombre)


class Therapist(Base):
    __tablename__ = 'therapist'
    id = Column(Integer, Sequence('therapist_id_seq'))
    nombre = Column(String(60))
    username = Column(String(20), primary_key=True)
    hash = Column(String(100))
    salt = Column(String(50))
    centro = Column(Integer)
    telefono = Column(String(20))
    profesion = Column(String(30))
    observaciones = Column(Text)
    fechaAlta = Column(String(20))

    session = relationship("Session", back_populates="therapist", cascade="all, delete")

    def __repr__(self):
        if self.nombre is not None and self.username is not None:
            return "<Therapist(name='%s %s')>" % (self.nombre, self.username)
        else:
            return "<Therapist(name='None None')>"


class Therapy(Base):
    __tablename__ = 'therapy'
    id = Column(Integer, Sequence('therapy_id_seq'), primary_key=True)
    name = Column(String(50))

    rounds = relationship("Round", back_populates="therapy", cascade="all, delete")

    def __repr__(self):
        return "<Therapy(name='%s: ')>" % (self.name)


class Round(Base):
    __tablename__ = 'round'
    id = Column(Integer, Sequence('round_id_seq'), primary_key=True)
    name = Column(String(50))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    session_id = Column(Integer, ForeignKey('session.id'))
    therapy_id = Column(Integer, ForeignKey('therapy.id'))

    therapy = relationship("Therapy", back_populates="rounds", cascade="all, delete")


    def __repr__(self):
        return "<Round(name='%s')>" % self.name



class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, Sequence('session_id_seq'), primary_key=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    patient_id = Column(Integer, ForeignKey('patient.username'))
    therapist_id = Column(Integer, ForeignKey('therapist.username'))

    patient = relationship("Patient", back_populates="session", cascade="all, delete")
    therapist = relationship("Therapist", back_populates="session", cascade="all, delete")

    def __repr__(self):
        if self.id is not None:
            return "<Session(id='%d')>" % self.id
        else:
            return "<Session(id = None)>"
