import openpyxl
import json
import io
import os
import openai
# import whisper
import pandas as pd
from streamlit_authenticator import Hasher
import yaml

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

    def __init__(self, logging = True, logging_path = "logging", exel_template = "form.xlsx", transcriptor = "api",
                 db_teacher_path = os.path.join("data", "teacher.csv"), db_students_path = os.path.join("data", "student.csv"), db_forms_path = os.path.join("data", "forms_meta.csv")):

        if transcriptor == "api":
            self.model = openai.OpenAI()
        #elif transcriptor == "local":
        #    self.model = whisper.load_model("small", in_memory = True )

        self.transcriptor = transcriptor

        self.teachers = pd.read_csv(db_teacher_path)
        self.students = pd.read_csv(db_students_path)
        self.forms_meta_path = db_forms_path
        self.forms_meta = pd.read_csv(db_forms_path)

        self.logging = logging
        self.logging_path = logging_path
        self.voice_loggs = os.path.join(logging_path, "recordings")
        self.transcript_loggs = os.path.join(logging_path, "transcripts")

        self.forms = os.path.join(logging_path, "forms")
        self.exel_template = exel_template

        if self.logging:
            if not os.path.isdir(self.logging_path):
                os.makedirs(self.voice_loggs)
                os.makedirs(self.forms)
                os.makedirs(self.transcript_loggs)

        self.parse_to_yaml()

    def parse_to_yaml(self):
        output_yaml = "config.yaml"
        if os.path.isfile(output_yaml):
            return
        # Load the CSV into a Pandas DataFrame
        df = self.teachers

        # Create the credentials dictionary
        credentials = {"usernames": {}}
        for _, row in df.iterrows():
            user_id = str(row["username"])
            credentials["usernames"][user_id] = {
                "email": row["email"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "logged_in": False,
                "password": row["password"],
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

    def dict_to_wb(self, wb_template, save_path, inputs):
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
        
        workbook.save(save_path)

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer

    def write_to_exel(self, inputs, exel_template_path=""):

        if self.is_valid_template(exel_template_path):
            template = exel_template_path
        elif self.is_valid_template(self.exel_template):
            template = self.exel_template
        else: 
            print("Invalid template - Nothing will be done")
            return
        
        path = self._get_unused_name(self.forms, template)
        print("Saving form: ", path)
        return self.dict_to_wb(template, path, inputs), path


    def _get_unused_name(self, folder, name):
            dir = os.listdir(folder)

            if not name in dir:
                return os.path.join(folder, name)
            
            for i in range(1, len(dir) + 2):
                file_name, extension = os.path.splitext(name)
                path = file_name + f"({i})" + extension
                if not path in dir:
                    return os.path.join(folder, path)

    def existing_teacher(self, id):
        return  id in self.dynamic_db['id'].values
    
    def existing_student(self, id):
        return id in self.dynamic_db['id'].values


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


if __name__=="__main__": 
     main()