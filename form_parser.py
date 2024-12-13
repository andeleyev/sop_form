import openpyxl
import json
import io
import os
import openai
# import whisper
import pandas as pd
from streamlit_authenticator import Hasher
import yaml
import re


import gdown
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import streamlit as st
from googleapiclient.discovery import build


# in secrets.toml service account
SERVICE_ACC_INFO = json.loads(st.secrets["google_credentials"]["json_content"])

# Define the scope for the APIs
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]

# Authenticate
credentials = Credentials.from_service_account_info(SERVICE_ACC_INFO, scopes=SCOPES)

# Define the field in the form where the inputs are
teacher_id = 'B6'
student_id = 'B7'
date_of_scenario = 'B8'

teacher_experience = 'B11'

student_age = 'B14'
teacher_exp_with_student = 'B15'
student_profile = 'B16'

situation = 'B19'
action_taken = 'B20'
effect = 'B21'
rating = 'B22'

class Parser():

    def __init__(self, logging = True, exel_template = "form.xlsx", transcriptor = "api"):

        if transcriptor == "api":
            self.model = openai.OpenAI()
        #elif transcriptor == "local":
        #    self.model = whisper.load_model("small", in_memory = True )

        self.transcriptor = transcriptor

        client =  gspread.authorize(credentials)
        self.client = client
        
        sheet_meta = client.open_by_key("1Rqw51AqqepG78FmrN1UqiWvwPS5ITpzSCA1Bx4WDmkU").sheet1
        data_meta = sheet_meta.get_all_values()
        self.forms_meta =pd.DataFrame(data_meta[1:], columns=data_meta[0])

        sheet_teacher = client.open_by_key("1l44B3aAaLWZhJOtWDjWkCLz89wTTk71fjai8_URV68k").sheet1
        data_teacher = sheet_teacher.get_all_values()
        self.teachers = pd.DataFrame(data_teacher[1:], columns=data_teacher[0])
        
        sheeet_student = client.open_by_key("1BcsZPL-CKhOmBYWc96cuK594Zau1anQhdaBCQTUAsHU").sheet1
        data_student = sheeet_student.get_all_values()
        self.students = pd.DataFrame(data_student[1:], columns=data_student[0])

        self.logging = logging
        self.voice_loggs = "17sNd1INEALhXbEiA5jklEu68SoZverUm"
        self.transcript_loggs = "1Axk6NkCyEUTcQWT_ldPPi3UoStEifQlL"

        self.forms = "forms"
        self.exel_template = exel_template

        self.parse_to_yaml()

    def parse_to_yaml(self):
        output_yaml = "config.yaml"
        if os.path.isfile(output_yaml):
            return
        # Load the CSV into a Pandas DataFrame
        df = self.teachers

        # Create the credentials dictionary
        credentials = {"usernames": {}}
        for i, row in df.iterrows():
            names = str(row['Име на учител']).split(" ")
            if len(names) >= 2:
                first, second = names[0], names[1] 
            else: 
                first, second = row['Име на учител'], " - "
            user_id = str(row["username"])
            credentials["usernames"][user_id] = {
                "email": row["Електронна Поща"],
                "first_name": first,
                "last_name": second,
                "logged_in": False,
                "password": row['pwd'],
            }

        # Create the YAML structure
        config = {
            "cookie": {
                "expiry_days": 5,
                "key": "jncjdjnjddedesaasd",  # Replace with your cookie key
                "name": "sop_form_cookie",
            },
            "credentials": credentials,
        }

        # Hash
        Hasher.hash_passwords(config['credentials'])

        # Write to YAML file
        with open(output_yaml, "w", encoding="utf-8") as yaml_file:
            yaml.dump(config, yaml_file, default_flow_style=False, sort_keys=False)    

    def is_valid_template(self, path):
        if not path.endswith("xlsx"):
            return False
        
        return os.path.isfile(path)

    def transcript_speech(self, speech_path):
        #if self.transcriptor == "local":
        #    result = self.model.transcribe(speech_path, language="bg")
        #    transcript = result["text"]
        #else:
            audio_file= open(speech_path, "rb")
            result = self.model.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language="bg"
            )
            transcript = result.text

            return transcript
    
    def wb_to_dict(self, path_form):
        workbook = openpyxl.load_workbook(path_form)
        sheet = workbook.active

        # Extract data manually
        data = {
            'teacher_id': sheet[teacher_id].value,
            'student_id': sheet[student_id].value,
            'date': sheet[date_of_scenario].value,
            'teacher_xp': sheet[teacher_experience].value,
            'student_age': sheet[student_age].value,
            'xp_with_child': sheet[teacher_exp_with_student].value,
            'student_profile': sheet[student_profile].value,
            'situation': sheet[situation].value,
            'action': sheet[action_taken].value,
            'effect': sheet[effect].value,
            'grade': sheet[rating].value
        }

        scenario = {
            "Student Profile": {
                "Age": student_age,
            },
            "Situation": situation,
            "Action Taken": action_taken,
            "Effectiveness in regards to the general aim": rating
        }

        return data, scenario

    def dict_to_wb(self, wb_template, inputs):
        workbook = openpyxl.load_workbook(wb_template)
        # Select the active worksheet
        sheet = workbook.active
            
        sheet[teacher_id] = inputs['teacher_id']
        sheet[student_id] = inputs['student_id']
        sheet[date_of_scenario] = inputs['date']
        sheet[teacher_experience] = inputs['teacher_xp']
        sheet[student_age] = inputs['student_age']
        sheet[teacher_exp_with_student] = inputs['xp_with_child']
        sheet[student_profile] = inputs['student_profile']
        sheet[situation] = inputs['situation']
        sheet[action_taken] = inputs['action']
        sheet[effect] = inputs['effect']
        sheet[rating] = inputs['grade']

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer

    def create_exel(self, inputs, exel_template_path=""):
        # Gets all field for the form.xlsx and return a workbook
        if self.is_valid_template(exel_template_path):
            template = exel_template_path
        elif self.is_valid_template(self.exel_template):
            template = self.exel_template
        else: 
            print("Invalid template - Nothing will be done")
            return
        
        return self.dict_to_wb(template, inputs)

    def extract_file_id(self, url):
        # Regular expression for Google Drive file ID
        file_id_pattern = r"(?:/d/|id=|open\?id=|uc\?id=)([a-zA-Z0-9_-]+)"
        match = re.search(file_id_pattern, url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid Google Drive URL")

    def get_filename(self, url):
        with build("drive", "v3", credentials=credentials) as service:
            file_id = self.extract_file_id(url)
            print(file_id)

            file_metadata = service.files().get(fileId=file_id, fields='name').execute()

        return file_metadata['name']

    def _get_unused_name(self, folder, name):
            dir = os.listdir(folder)

            if not name in dir:
                return os.path.join(folder, name)
            
            for i in range(1, len(dir) + 2):
                file_name, extension = os.path.splitext(name)
                path = file_name + f"({i})" + extension
                if not path in dir:
                    return os.path.join(folder, path)

    def add_from_to_db(self, from_path, t_id, audio_sit, audio_act, audio_eff, script_sit, script_act, script_eff,  s_id, date, time):
        # row = form_id,from_path,date,time,audio_sit,audio_action,audio_effect,transcript_sit,transcript_action,transcript_effect,teacher_id,student_id
        print(time)
        form_id = hash(t_id + s_id + date + time) 

        new_row = [form_id, from_path, date, time,
                   audio_sit, audio_act, audio_eff,
                   script_sit, script_act, script_eff, 
                   t_id, s_id]
       

        db = self.forms_meta

        if form_id not in db['form_id'].to_list():
            db.loc[len(db)] = new_row
            print("Updating the form meta database")
            db.to_csv(self.forms_meta_path, index=False)