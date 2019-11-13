#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from bbdd import *
from datetime import datetime

if __name__ == '__main__':
    bbdd = BBDD()

    # create database
    bbdd.create_database("prueba_therapy.db")
    #or open an existing one
#    bbdd.open_database("prueba.db")

    #write
    result, patient = bbdd.new_patient(username='andreslopez', nombre="Andres Lopez", sexo= "Varón", edad=87, datosRegistro="", nivelCognitivo= 7, nivelFisico=4, nivelJuego=2, centro="Caceres", profesional="otro", observaciones="...", fechaAlta="20191022")
    result, patient2 = bbdd.new_patient(username='elenamartinez', nombre="'Elena Martinez'", sexo="Mujer", edad=67, datosRegistro="...", nivelCognitivo= 6, nivelFisico=8, nivelJuego=9, centro="Badajoz", profesional="este", observaciones="---", fechaAlta="20191021")

    # #read
    # result, out_pat = bbdd.get_patient_by_username('andreslopez')
    # print(result, out_pat)
    #
    # #delete
    # result = bbdd.remove_patient("elenamartinez")
    # print("Delete Elena", result)
    #
    # #read all
    # pat_list = bbdd.get_all_patients()
    # print("All patients")
    # for pat in pat_list:
    #     print(pat)

    #therapist
    result, therapist = bbdd.new_therapist(nombre="Luis Perez", username="luisperez" , hash="$pbkdf2-sha256$29000$Qegdg9Aa45xzzhkjxFgL4Q$T2WhJc.EeWDVIH1WAmwsFbeG5ELdTe5pClMZthcoMgU" , salt="" , centro="Badajoz" , telefono="927296677" , profesion="Terapeuta" , observaciones="todas" , fechaAlta="20191010")

    #game
    game = bbdd.new_game("Elevacion brazos")
    game = bbdd.new_game("Sentadillas")

    # #session
    # time = datetime.now()
    # result, session = bbdd.new_session(time, time, patient, therapist)
    # print(session)
    #
    # time = datetime.now()
    # result, session = bbdd.new_session(time, time, patient2, therapist)
    #
    #
    # #get all session from therapist
    # session_list = bbdd.get_all_session_by_therapist_username("luisperez")
    # print("All session from Luis")
    # for s in session_list:
    #     print(s)


