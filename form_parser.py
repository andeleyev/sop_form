import openpyxl
import json
import io
import os
import openai
#from speechmatics.models import ConnectionSettings, BatchTranscriptionConfig
#from speechmatics.batch_client import Batcheent
# import whisper
from datetime import datetime
import openpyxl.styles
import pandas as pd
from streamlit_authenticator import Hasher
import yaml
import re

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload



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

    def __init__(self, logging = True, exel_template = "form.xlsx", transcriptor = "openai_api"):

        if transcriptor == "openai_api":
            self.speech_client = openai.OpenAI()
        #elif transcriptor == "whisper":
        #    self.model = whisper.load_model("small", in_memory = True )

        # Can be openai_api, whisper or speechmatics
        self.transcriptor = transcriptor

        client =  gspread.authorize(credentials)
        self.client = client
        
        self.meta_sheet_id = "1Rqw51AqqepG78FmrN1UqiWvwPS5ITpzSCA1Bx4WDmkU"
        self.sheet_meta = client.open_by_key("1Rqw51AqqepG78FmrN1UqiWvwPS5ITpzSCA1Bx4WDmkU").sheet1
        data_meta = self.sheet_meta.get_all_values()
        self.forms_meta = pd.DataFrame(data_meta[1:], columns=data_meta[0])

        self.sheet_teacher = client.open_by_key("1l44B3aAaLWZhJOtWDjWkCLz89wTTk71fjai8_URV68k").sheet1
        data_teacher = self.sheet_teacher.get_all_values()
        self.teachers = pd.DataFrame(data_teacher[1:], columns=data_teacher[0])
        
        self.sheet_id_students = "1BcsZPL-CKhOmBYWc96cuK594Zau1anQhdaBCQTUAsHU"
        self.sheeet_student = client.open_by_key("1BcsZPL-CKhOmBYWc96cuK594Zau1anQhdaBCQTUAsHU").sheet1
        data_student = self.sheeet_student.get_all_values()
        self.students = pd.DataFrame(data_student[1:], columns=data_student[0])

        self.logging = logging
        self.voice_loggs = "17sNd1INEALhXbEiA5jklEu68SoZverUm"
        self.exel_folder = "1W9Ae2y8Lc1xHy8X3L6Ke6lkT9e_lZQUS"

        self.exel_template = exel_template

        self.parse_to_yaml()

    def parse_to_yaml(self):
        output_yaml = "config.yaml"
        if os.path.isfile(output_yaml):
            os.remove(output_yaml)
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
            pwd = row["pwd"].strip()
            credentials["usernames"][user_id] = {
                "email": row["Електронна Поща"],
                "first_name": first,
                "last_name": second,
                "logged_in": False,
                "password": pwd,
            }
            # print(row["username"],":",pwd, sep="")

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
        #elif
        #if self.transcriptor == "openai_api":
            audio_file= open(speech_path, "rb")
            result = self.speech_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="bg"
            )
            transcript = result.text

            return transcript
        #elif self.transcriptor == "speechmatics":
        #    pass

    def get_xp_together(self, sid, tid):
        df = self.forms_meta

        #print(sid, type(sid), tid, type(tid))
        df = df.loc[(df['teacher_id'] == str(tid)) & (df['student_id'] == str(sid))].copy()
        #print(result)
        df['datetime'] = pd.to_datetime(df['creation_date'] + ' ' + df['creation_time'], format='%d-%m-%Y %H:%M')
        df.replace('None', pd.NA, inplace=True)
        df = df.sort_values('datetime', ascending=False)
        
        if df.empty:
            return None
        else:
            result = df.iloc[0]
            return str(result['xp_together'])

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
        # Hyperlink fo the karta
        if inputs['student_profile'] == "":
            sheet[student_profile] = ""
        else:
            hyper = f'=HYPERLINK("{inputs['student_profile']}", "{"Линк Карта Функтионална оценка"}")'
            sheet[student_profile] = hyper

        sheet[situation] = inputs['situation']
        sheet[action_taken] = inputs['action']
        sheet[effect] = inputs['effect']
        sheet[rating] = inputs['grade']

        sheet.protection = openpyxl.worksheet.protection.SheetProtection(
            sheet=True,
            formatCells=False,
            formatColumns=False,
            formatRows=False,
            insertColumns=False,
            insertRows=False,
            insertHyperlinks=False,
            deleteColumns=False,
            deleteRows=False,
            sort=False,
            autoFilter=False,
            pivotTables=False
        )

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
        exel = self.dict_to_wb(template, inputs)
        return exel
    
    # ================================================================================
    #       Google Drive Fuctionalities - General
    # ================================================================================
    def reload(self):
        self.student_sheet = self.client.open_by_key(self.sheet_id_students).sheet1
        data_student = self.sheeet_student.get_all_values()
        self.students = pd.DataFrame(data_student[1:], columns=data_student[0])

        self.sheet_meta = self.client.open_by_key(self.meta_sheet_id).sheet1
        data_meta = self.sheet_meta.get_all_values()
        self.forms_meta = pd.DataFrame(data_meta[1:], columns=data_meta[0])



    def create_google_drive_link(self, file_id):
        link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        return link

    def extract_file_id(self, url):
        # Regular expression for Google Drive file ID
        file_id_pattern = r"(?:/d/|id=|open\?id=|uc\?id=)([a-zA-Z0-9_-]+)"
        match = re.search(file_id_pattern, url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid Google Drive URL")

    def upload_doc_drive(self, file_path, parent_folder):
        # Upload the File at 'file_path' to the google drive folder with id: 'parent_folder'
        #try:
            with build("drive", "v3", credentials=credentials) as service:            
                file_metadata = {'name': os.path.basename(file_path), "parents": [parent_folder]}
                media = MediaFileUpload(file_path, resumable=True)
                
                file = service.files().create(
                    body=file_metadata, 
                    media_body=media, 
                    fields='id'
                ).execute()
            
            return file.get('id')
        #except Exception as e:
        #    st.error(f"Error uploading file: {e}")
        #    return None
        
    def download_doc_from_drive(file_id, destination):
        """Downloads a file from Google Drive."""
        with build("drive", "v3", credentials=credentials) as service: 
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination, 'wb')  # Open a local file to save content
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")

            print(f"File downloaded to {destination}")

    def get_filename(self, url):
        # Extract the file name from the url to the file in Drive
        try:
            with build("drive", "v3", credentials=credentials) as service:
                file_id = self.extract_file_id(url)
                # print(file_id)
                file_metadata = service.files().get(fileId=file_id, fields='name').execute()

            return file_metadata['name']
        except ValueError:
            return None
 
    # ================================================================================
    #       Google Drive Fuctionalities - Specific
    # ================================================================================

    def karta_to_drive(self, file_path):
        """Upload card functional grade to Google Drive."""

        folder_cards = "1F2oiBQzZt1ko7DhaVIeO4VR-5RrJDNlk"
        file_id = self.upload_doc_drive(file_path, folder_cards)
        
        return file_id     
    
    def upload_exel(self, exel, corresponding_json_id):
        name = f"form_{corresponding_json_id}.xlsx"

        with open(name, "wb") as f:
            f.write(exel.getvalue())

        self.upload_doc_drive(name, self.exel_folder)
        os.remove(name)

    def save_scenario(self, dict, file_name):
        with open(file_name, 'w') as json_file:
            json.dump(dict, json_file, indent=4, ensure_ascii=False)
        
        # Prepare file metadata
        folder_scenario = "1HeAv4-zn--7IUxZZY4MgMb2lb_YdFCsD"
        file_id = self.upload_doc_drive(file_name, folder_scenario)

        os.remove(file_name)
        return file_id

    def add_student_to_db(self, student, teacher_id, student_id):
        student['date of entry'] = datetime.now().strftime('%d-%m-%Y %H:%M')
        student['id teacher'] = teacher_id
        student['id student'] = str(student_id)

        self.students.loc[len(self.students)] = student
        last_row = self.students.iloc[-1].tolist()
        self.sheeet_student.append_row(last_row)

    def add_form_to_db(self, form, t_id, audio_sit, audio_act, audio_eff, script_sit, script_act, script_eff,  s_id, xp_together):
        # row = form_id,from_path,date,time,audio_sit,audio_action,audio_effect,transcript_sit,transcript_action,transcript_effect,teacher_id,student_id
        time = datetime.now()

        cr_date, cr_time = time.strftime("%d-%m-%Y"), time.strftime("%H:%M")

        if script_sit == "":
            script_sit = "empty"
        if script_act == "":
            script_act = "empty"
        if script_eff == "":
            script_eff = "empty"

        recording_folder = "17sNd1INEALhXbEiA5jklEu68SoZverUm"

        if audio_sit != "None" and os.path.isfile(audio_sit):
            audio_sit_id = self.upload_doc_drive(audio_sit, recording_folder)
            os.remove(audio_sit)
            audio_sit = self.create_google_drive_link(audio_sit_id)

        if audio_act != "None" and os.path.isfile(audio_act):
            audio_act_id = self.upload_doc_drive(audio_act, recording_folder)
            os.remove(audio_act)
            audio_act = self.create_google_drive_link(audio_act_id)
            
        if audio_eff != "None" and os.path.isfile(audio_eff):
            audio_eff_id = self.upload_doc_drive(audio_eff, recording_folder)
            os.remove(audio_eff)
            audio_eff = self.create_google_drive_link(audio_eff_id)
           


        drive_form_id = self.save_scenario(form, f"scenario.json")

        form['id'] = drive_form_id

        

        new_row = [str(self.create_google_drive_link(drive_form_id)), cr_date, cr_time,
                   audio_sit, audio_act, audio_eff,
                   script_sit, script_act, script_eff, 
                   t_id, str(s_id), xp_together]
       
        #for i in new_row:
        #    print(type(i))


        print("Updating the form meta database")
        self.sheet_meta.append_row(new_row)

        return drive_form_id
    

    '''
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
                "Age": data[student_age],
            },
            "Situation": situation,
            "Action Taken": action_taken,
            "Effectiveness in regards to the general aim": rating
        }

        return data, scenario
    '''
    
