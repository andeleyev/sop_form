import streamlit as st
import datetime
import form_parser
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from streamlit_extras.bottom_container import bottom
import io

st.set_page_config(page_title="SOP Form Parser", page_icon="🗣️", layout="centered", initial_sidebar_state="auto", menu_items=None)

api = st.secrets["general"]["api_key"]


now = datetime.datetime.now()
today = now.strftime("%d-%m-%Y")

@st.cache_resource
def initialize(key):
    os.environ["OPENAI_API_KEY"] = key
    parser = form_parser.Parser()

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    return parser, config

parser, config = initialize(api)

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

    st.session_state['ti_xp'] = str(teacher['work_experience'].values[0])
    return teacher

@st.cache_resource
def get_student_data(id):
    global parser
    students = parser.students

    student = students.loc[students['id'] == int(id)]
    # print(student)
    if not student.empty:
        st.session_state['ti_age'] = str(student['age'].values[0])
        st.session_state['ti_profile'] = str(student['profile'].values[0])
    else:
        st.warning("Did not find the student in the database")

    return student

# Pre-hashing all plain text passwords once
#hashed = stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False
)

if not "counter" in st.session_state:
    st.session_state.counter = 0

#if "ti_teacher_id" not in st.session_state: THis better later
#    st.session_state["ti_teacher_id"] = ""
if "ti_student_id" not in st.session_state:
    st.session_state["ti_student_id"] = ""
if "text_sit" not in st.session_state:
    st.session_state["text_sit"] = ""
if "text_act" not in st.session_state:
    st.session_state["text_act"] = ""
if "text_eff" not in st.session_state:
    st.session_state["text_eff"] = ""
if "grade_slider" not in st.session_state:
    st.session_state["grade_slider"] = 5
if "ti_xp" not in st.session_state:
    st.session_state["ti_xp"] = ""   
if "ti_age" not in st.session_state:
    st.session_state["ti_age"] = ""
if "ti_xp_toghether" not in st.session_state:
    st.session_state["ti_xp_toghether"] = ""
if "ti_profile" not in st.session_state:
    st.session_state["ti_profile"] = ""
if "audi_sit" not in st.session_state:
    st.session_state["audi_sit_key"] = "sit" + str(st.session_state['counter'])
if "audi_act" not in st.session_state:
    st.session_state["audi_act_key"] = "act" + str(st.session_state['counter'])
if "audi_eff" not in st.session_state:
    st.session_state["audi_eff_key"] = "eff" + str(st.session_state['counter'])


def reset_state():
    print("resetting !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    st.session_state.counter += 1
    st.session_state["audi_eff_key"] = "eff" + str(st.session_state['counter'])
    st.session_state["audi_act_key"] = "act" + str(st.session_state['counter'])
    st.session_state["audi_sit_key"] = "sit" + str(st.session_state['counter'])

    # st.session_state["tid"] = ""
    st.session_state["sid"] = ""

    st.session_state["text_sit"] = ""
    st.session_state["text_act"] = ""
    st.session_state["text_eff"] = ""
    st.session_state["grade"] = 3

    # st.session_state["ti_xp"] = ""
    st.session_state["ti_age"] = ""
    st.session_state["ti_xp_toghether"] = ""
    st.session_state["ti_profile"] = ""

    st.session_state["audi_sit"] = ""
    st.session_state["audi_act"] = ""
    st.session_state["audi_eff"] = ""


if not "download" in st.session_state:
    st.session_state.download = False

if st.session_state['download']:
    with bottom():
        d1, d2 = st.columns(2)

        with d1:
            downloaded = st.download_button("изтегляне на попълнения формуляр", type="primary", use_container_width=True, data=st.session_state.exel, file_name="filled_form.xlsx")
        with d2:
            reset = st.button("попълни нов формулар", type="primary", use_container_width=True)

        if reset:
            st.session_state.download = False
            print("resetingggg")
            reset_state()
            st.rerun()


authenticator.login(fields={'Form name':'Login', 'Username':'вашето потребителско име', 'Password':'парола', 'Login':'Login', 'Captcha':'Captcha'})

if st.session_state['authentication_status']:
    st.write(f'Welcome *{st.session_state["name"]}*')

    username = st.session_state["username"]
    
    logged_teacher = get_teacher_data(username)  
    logged_teacher_id = str(logged_teacher['id'].values[0])
    
    
    if "tid" not in st.session_state:
        st.session_state["tid"] = logged_teacher_id
    # Title of the application
    # '# Въпросник "Ситуации соп" '
    '# Бланка за описване на ситуация и реакция при работа с деца със СОП'
    # "###### Формулар за събиране на ситуации относно индивидуалните прояви и предизвикателства при деца с аутизъм"

    " "
    teacher_form = logged_teacher

    # Speech input button
    # audio_st = st.audio_input("🎤 Говори", key=f"voice_input_{st.session_state.audio_key}")

    @st.cache_data
    def transcribe(audio, name):
        if not audio:
            return "", "None"

        global parser
        audio_path = parser._get_unused_name(parser.voice_loggs, name)

        # Method 2: Using getvalue()
        audio_bytes = audio.getvalue()
        audio_file = io.BytesIO(audio_bytes).
        #with open(audio_path, "wb") as file:
        #    print("saving audio: ", audio_path)
        #    file.write(audio.getvalue())
        
        script = parser.transcript_speech(audio_file)
        return script, "None"

    # Form layout
    st.markdown("## Идентификационна информация\n\n ##### Вашият уникален анонимен идентификатор:")
    st.text_input("a", key="tid", label_visibility="collapsed")
    if st.session_state["tid"] != "" and int(st.session_state["tid"]) != logged_teacher_id:
        teacher_form = get_teacher_data(id=st.session_state["tid"])

    st.markdown("##### Уникален анонимен номер на детето:")
    st.text_input("b", key="sid", label_visibility="collapsed")
    if st.session_state["sid"]:
        student = get_student_data(int(st.session_state["sid"]))

    "##### Дата на случката:"   
    date = st.date_input("Дата на случката:", format="DD.MM.YYYY", label_visibility="collapsed") # remove default to make it today


    "## Ситуация и реакция "
    "  "
    "#### **Опишете устно или писмено ситуацията, която се е случила:**"
    "(за гласов запис натиснете микрофона)"
    a1, a2 = st.columns([5, 1])

    with a2:
        audio_sit = st.audio_input("aa", key=st.session_state["audi_sit_key"], label_visibility="collapsed")
        transcript_sit, audio_sit_path = transcribe(audio_sit, f"situation_audio_{today}.mp3")
        if transcript_sit != "":
            print("test")
            st.session_state["text_sit"] = transcript_sit
    with a1:
        st.text_area("ситуацията", key="text_sit", placeholder="write here", height=257, label_visibility="collapsed")

    "  "
    "#### **Опишете устно или писмено Вашата реакция:**"
    "(за гласов запис натиснете микрофона)"
    b1, b2 = st.columns([5, 1])
    with b2:
        audio_act = st.audio_input("действия", key=st.session_state["audi_act_key"], label_visibility="collapsed")
        transcript_act, audio_act_path = transcribe(audio_act, f"action_audio_{today}.mp3")
        if transcript_act != "":
            st.session_state["text_act"] = transcript_act
    with b1:
        st.text_area("реакцията", key="text_act", height=257, label_visibility="collapsed")

    "#### Опишете устно или писмено **ефекта** от Вашата реакция:"
    "(за гласов запис натиснете микрофона)",
    c1, c2 = st.columns([5, 1])
    with c2:
        audio_eff = st.audio_input("как се е развила ситуацията", key=st.session_state["audi_eff_key"], label_visibility="collapsed")
        transcript_eff, audio_eff_path = transcribe(audio_eff, f"effect_audio_{today}.mp3")
        if transcript_eff != "":
            st.session_state["text_eff"] = transcript_eff
    with c1:
        st.text_area("Опишете ефекта от вашата реакция:", key="text_eff", height=257, label_visibility="collapsed")

    st.markdown("#### Оценете ефекта от вашата реакция от 1 до 10:")
    #e1, e2 = st.columns([5, 1])
    #with e1:
    #    st.markdown("#### Оценете ефекта от вашата реакция от 1 до 10:")
    #with e2:
    #    st.info("инфо")
    
    explain_grades = """# whaat
    aint no way
    aаааааааааin no way

    that going fucking viral
    """
    st.slider("(за повече информацуя натиснете вапроцителния знак) ", 1, 5, key="slider", help=explain_grades, label_visibility="visible")

    st.markdown("## Информация за специалиста и детето \n\n #### Колко години опит имате:")
    st.text_input("Колко години опит имате:", key="ti_xp", label_visibility="collapsed")

    st.markdown("#### На колко години е детето:")
    st.text_input("На колко години е детето:", key="ti_age", label_visibility="collapsed")


    st.markdown("#### От колко години работите с това дете:")
    st.text_input("От колко години работите с това дете:", key="ti_xp_toghether", label_visibility="collapsed")

    st.markdown("#### Какъв е профилът на детето? / Какъв е линкът към досието му:")
    st.text_input("профилът", key="ti_profile", label_visibility="collapsed")

    st.markdown(" ")

    submit = st.button("подаване на формуляр", type="primary", use_container_width=True)

    if not "ballons" in st.session_state:
        st.session_state.balloons = False

    if st.session_state.balloons:
        st.session_state.balloons = False
        st.balloons()
        st.toast("Формулара е испратен", icon='🥳') 

    if submit:
        st.session_state.download = True

        inputs = {
            "teacher_id": st.session_state["tid"],
            "student_id": st.session_state["sid"],
            "date": date.strftime("%d-%m-%Y"),
            "teacher_xp": st.session_state["ti_xp"],
            "student_age": st.session_state["ti_age"],
            "xp_with_child": st.session_state["ti_xp_toghether"],
            "student_profile": st.session_state["ti_profile"],
            "situation": st.session_state["text_sit"],
            "action": st.session_state["text_act"],
            "effect": st.session_state["text_eff"],
            "grade": st.session_state['slider']
        }

        exel, exel_path = parser.write_to_exel(inputs)
        if not exel is None:
            st.session_state.balloons = True
        st.session_state.exel = exel
        # print(st.session_state.exel)
        time = now.strftime('%H:%M')

        parser.add_form_to_db(exel_path, st.session_state["tid"], audio_sit_path, audio_act_path, audio_eff_path, 
                                transcript_sit, transcript_act, transcript_eff, st.session_state["ti_student_id"], date.strftime("%d-%m-%Y"), time)

        
        st.rerun()


elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
