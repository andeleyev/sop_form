import streamlit as st
import datetime
import form_parser
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="SOP Form Parser", page_icon="🧪", layout="centered", initial_sidebar_state="auto", menu_items=None)


now = datetime.datetime.now()
today = now.strftime("%d-%m-%Y")

@st.cache_resource
def initialize():
    parser = form_parser.Parser(transcriptor="local")
    return parser

parser = initialize()

@st.cache_resource
def get_teacher_data(username=None, id=None):
    global parser
    teachers = parser.teachers
    # print(teachers)
    if username == None and id == None:
        print("No username or id were provided to get teacher")
        return

    if username is None:
        teacher = teachers.loc[teachers["id"] == int(id)]
    else:
        print(id)
        teacher = teachers.loc[teachers['username'] == username]
    print("Teacher: ", teacher)
    return teacher

@st.cache_resource
def get_student_data(id):
    global parser
    students = parser.students

    student = students.loc[students['id'] == int(id)]
    print(student)
    if not student.empty:
        st.session_state['ti_age'] = str(student['age'].values[0])
        st.session_state['ti_profile'] = str(student['profile'].values[0])
    else:
        st.warning("Did not find the student in the database")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
#hashed = stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False
)

authenticator.login(fields={'Form name':'Login', 'Username':'Вашия ИД', 'Password':'Парола', 'Login':'Login', 'Captcha':'Captcha'})

if st.session_state['authentication_status']:
    st.write(f'Welcome *{st.session_state["name"]}*')

    username = st.session_state["username"]
    
    logged_teacher = get_teacher_data(username)  
    logged_teacher_id = str(logged_teacher['id'].values[0])
    
    # Title of the application
    st.title("Autism Scenario Questionnaire")
    teacher_form = logged_teacher

    if 'downlaod' not in st.session_state:
        st.session_state.download = False

    # Speech input button
    # audio_st = st.audio_input("🎤 Говори", key=f"voice_input_{st.session_state.audio_key}")

    @st.cache_data
    def transcribe(audio, name):
        if not audio:
            return "", "None"

        global parser
        audio_path = parser._get_unused_name(parser.voice_loggs, name)
        with open(audio_path, "wb") as file:
            print("saving audio: ", audio_path)
            file.write(audio.getvalue())
        

        script = parser.transcript_speech(audio_path)
        return script, audio_path

    # Form layout
    st.subheader("Идентификационна информация")
    teacher_id = st.text_input("Вашият уникален анонимен идентификатор:", key="ti_teacher_id", value=logged_teacher_id)
    if teacher_id != logged_teacher_id:
        teacher_form = get_teacher_data(id=teacher_id)

    def_teacher_xp = teacher_form['work_experience'].values[0]

    student_id = st.text_input("Уникален анонимен номер на детето:", key="ti_student_id")
    if student_id:
        student = get_student_data(student_id)
    date = st.date_input("Дата на случката:", key="date", format="DD.MM.YYYY") # remove default to make it today


    st.subheader("Ситуация и реакция ")
    audio_sit = st.audio_input("говори за ситуацуята")
    transcript_sit, audio_sit_path = transcribe(audio_sit, f"situation_audio_{today}.mp3") 
    situation = st.text_area("Опишете ситуацията, която се е случила:", key="tf_situation", value=transcript_sit)

    audio_act = st.audio_input("говори за какви действия предприехте")
    transcript_act, audio_act_path = transcribe(audio_act, f"action_audio_{today}.mp3")
    action = st.text_area("Опишете реакцията, която сте предприели:", key="tf_action", value=transcript_act)

    audio_eff = st.audio_input("как се е развила ситуацията")
    transcript_eff, audio_eff_path = transcribe(audio_eff, f"effect_audio_{today}.mp3")
    effect= st.text_area("Опишете ефекта от вашата реакция:", key="tf_effect", value=transcript_eff)

    grade= st.slider("Оценете ефекта от вашата реакция от 1 до 10:", 1, 10, 5, key="slider")

    st.subheader("Информация за ресурсния учител")
    teacher_xp = st.text_input("Колко години опит имате:", key="ti_teacher_xp", value=def_teacher_xp)

    st.subheader("Информация за детето")
    student_age = st.text_input("На колко години е детето:", key="ti_age")
    xp_with_student = st.text_input("От колко години работите с това дете:", key="ti_xp_with_student")
    profile = st.text_input("Какъв е профилът на детето? / Какъв е линкът към досието му:", key="ti_profile")



    submit = st.button("Submit")

    if submit or st.session_state['download']:

        
        st.session_state.download = True

        if submit:
            inputs = {
                "teacher_id": teacher_id,
                "student_id": student_id,
                "date": date.strftime("%d-%m-%Y"),
                "teacher_xp": teacher_xp,
                "student_age": student_age,
                "xp_with_child": xp_with_student,
                "student_profile": profile,
                "situation": situation,
                "action": action,
                "effect": effect,
                "grade": grade,
            }
    
            exel, exel_path = parser.write_to_exel(inputs)
            st.session_state.exel = exel
            # print(st.session_state.exel)
            time = now.strftime('%H:%M')

            if transcript_sit == "":
                transcript_sit = "empty"
            if transcript_act == "":
                transcript_act = "empty"
            if transcript_sit == "":
                transcript_act = "empty"

            parser.add_from_to_db(exel_path, teacher_id, audio_sit_path, audio_act_path, audio_eff_path, transcript_sit, transcript_act, transcript_eff, student_id, date.strftime("%d-%m-%Y"), time)

        downloaded = st.download_button("изтегляне на попълнения формуляр", data=st.session_state.exel, file_name="filled_form.xlsx")
        reset = st.button("reset")
        if downloaded or reset:
            st.session_state.ti_teacher_id = ""
            st.session_state.ti_student_id = ""

            st.session_state.tf_situation = ""
            st.session_state.tf_action = ""
            st.session_state.tf_effect = ""
            st.session_state.slider = 5

            st.session_state.ti_teacher_xp = ""
            st.session_state.ti_age = ""
            st.session_state.ti_xp_with_student = ""
            st.session_state.ti_profile = ""

            st.session_state.download = False

            st.rerun()


elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
