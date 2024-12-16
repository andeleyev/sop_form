import streamlit as st
import datetime
import form_parser
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_extras.stylable_container import stylable_container
import os
from streamlit_extras.bottom_container import bottom
# from st_audiorec import st_audiorec
from audio_recorder_streamlit import audio_recorder

st.set_page_config(page_title="SOP Form Parser", page_icon="🗣️", layout="centered", initial_sidebar_state="auto", menu_items=None)

api = st.secrets["general"]["api_key"]


now = datetime.datetime.now()
today = now.strftime("%d-%m-%Y")

@st.cache_resource
def initialize(key):
    os.environ["OPENAI_API_KEY"] = key
    parser = form_parser.Parser()
    students = parser.students
    ids = students['Идентификационен номер'].values
    return parser, ids

parser, student_ids = initialize(api)

@st.cache_resource
def get_teacher_data(username):
    global parser
    teachers = parser.teachers

    teacher = teachers.loc[teachers['username'] == username]
    print("Teacher: ", teacher)

    if not teacher.empty:
        diff = now.year - int(teacher['Ресурсен учител от година'].values[0])
        teacher_xp = f"{diff}-{diff + 1}"
        teacher_id = teacher['Идентификационен номер на учител'].values[0]
    else:
        st.warning("Did not find the teacher in the database")

    return teacher_id, teacher_xp, 

@st.cache_resource
def get_student_data(id):
    global parser
    students = parser.students
    student = students.loc[students['Идентификационен номер'] == str(id)]
    print(student)
    sp = dict()
    if not student.empty:
        student = student.iloc[-1]
        sp['age'] = (now.year - int(student['Година на раждане']))

        sp['url'] = str(student['линк към файл с профил'])
        # print(url)
        st.session_state['ti_profile'] = sp['url']
        file = parser.get_filename(sp['url'])
        if file == None:
            file = "link"
        st.session_state['profile_filename'] = file

        sp['autism'] = bool(int(student['аутизъм']))
        sp['dislexia'] = bool(int(student['дислекция']))
        sp['ns1'] = bool(int(student['нз1']))
        sp['ns2'] = bool(int(student['нз2']))
        sp['ns3'] = bool(int(student['нз3']))
        sp['ns4'] = bool(int(student['нз4'])) 
        sp['ns5'] = bool(int(student['нз5'])) 
        sp['ns6'] = bool(int(student['нз6'])) 
        sp['ns7'] = bool(int(student['нз7'])) 
        sp['ns8'] = bool(int(student['нз8'])) 
        sp['ns9'] = bool(int(student['нз9']))        
        sp['ns10'] = bool(int(student['нз10'])) 
        sp['ns11'] = bool(int(student['нз11']))
        sp['ns12'] = bool(int(student['нз12'])) 

        st.session_state['autism'] = sp['autism']
        st.session_state['dislexia'] = sp['dislexia']
        st.session_state['ns1'] = sp['ns1']
        st.session_state['ns2'] = sp['ns2'] 
        st.session_state['ns3'] = sp['ns3'] 
        st.session_state['ns4'] = sp['ns4'] 
        st.session_state['ns5'] = sp['ns5'] 
        st.session_state['ns6'] = sp['ns6'] 
        st.session_state['ns7'] = sp['ns7'] 
        st.session_state['ns8'] = sp['ns8'] 
        st.session_state['ns9'] = sp['ns9']     
        st.session_state['ns10'] = sp['ns10']
        st.session_state['ns11'] = sp['ns11']
        st.session_state['ns12'] = sp['ns12']

    else:
        st.warning("Did not find the student in the database")
        return None, None

    return sp, file

# Login in Funitonality
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

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
#if "profile_filename" not in st.session_state:
#    st.session_state["profile_filename"] = ""

if "text_sit" not in st.session_state:
    st.session_state["text_sit"] = ""
if "text_act" not in st.session_state:
    st.session_state["text_act"] = ""
if "text_eff" not in st.session_state:
    st.session_state["text_eff"] = ""

if "ti_xp_toghether" not in st.session_state:
    st.session_state["ti_xp_toghether"] = ""

if "ti_profile" not in st.session_state:
    st.session_state["ti_profile"] = ""

if "audi_sit_keys" not in st.session_state:
    st.session_state["audi_sit_key"] = "sit" + str(st.session_state['counter'])
if "audi_act_key" not in st.session_state:
    st.session_state["audi_act_key"] = "act" + str(st.session_state['counter'])
if "audi_eff_key" not in st.session_state:
    st.session_state["audi_eff_key"] = "eff" + str(st.session_state['counter'])


    
def reset_state():
    print("resetting !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    st.session_state.counter += 1
    st.session_state["audi_eff_key"] = "eff" + str(st.session_state['counter'])
    st.session_state["audi_act_key"] = "act" + str(st.session_state['counter'])
    st.session_state["audi_sit_key"] = "sit" + str(st.session_state['counter'])

    st.session_state["sid"] = ""

    st.session_state["text_sit"] = ""
    st.session_state["text_act"] = ""
    st.session_state["text_eff"] = ""
    st.session_state["grade"] = 3

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
    st.write(f'Добре дошли *{st.session_state["name"]}* ')

    username = st.session_state["username"]
    teacher_id, teacher_xp = get_teacher_data(username)  

    st.write(f"Вашият Идентификатор: {teacher_id}")
    
    # Title of the application
    # '# Въпросник "Ситуации соп" '
    '# Бланка за описване на ситуация и реакция при работа с деца със СОП'
    # "###### Формулар за събиране на ситуации относно индивидуалните прояви и предизвикателства при деца с аутизъм"

    " "

    # Speech input button
    # audio_st = st.audio_input("🎤 Говори", key=f"voice_input_{st.session_state.audio_key}")

    @st.cache_data
    def transcribe(audio, audio_path):
        if not audio:
            return "", "None"

        global parser

        with open(audio_path, "wb") as file:
            print("saving audio: ", audio_path)
            file.write(audio)
        

        script = parser.transcript_speech(audio_path)
        return script, audio_path

    # Form layout
    #st.markdown("## Идентификационна информация\n\n ##### Вашият уникален анонимен идентификатор:")
    #st.text_input("a", key="tid", label_visibility="collapsed")
    #if st.session_state["tid"] != "" and int(st.session_state["tid"]) != logged_teacher_id:
    #    teacher_form = get_teacher_data(id=st.session_state["tid"])

    st.markdown("##### Уникален анонимен номер на детето:")
    s = st.selectbox("b", student_ids, key="sid", label_visibility="collapsed", index=None)
    
    if s:
        student_pr, file = get_student_data(int(st.session_state["sid"]))
        new_student_pr = student_pr.copy()
        if file == "link":
            st.toast("The URL to the student card could not be loaded correctly", icon="❗")

    st.markdown("#### От колко години работите с това дете:")
    st.text_input("От колко години работите с това дете:", key="ti_xp_toghether", label_visibility="collapsed")


    "## Ситуация и реакция "
    "  "
    "##### Дата на :rainbow[случката:]"   
    date = st.date_input("Дата на :rainbow[случката]:", format="DD.MM.YYYY", label_visibility="collapsed") # remove default to make it today


    "#### **Опишете устно или писмено ситуацията, която се е случила:**"
    "(за гласов запис натиснете микрофона)"
    a1, a2 = st.columns([7, 1])

    with a2:
        #with stylable_container(
        #    key="orange",
        #    css_styles="""
        #        button {
        #            background-color: green;
        #            color: white;
        #            border-radius: 20px;
        #        }
        #        """,
        #):  
        #    audio_sit = st.audio_input("aa", key=st.session_state["audi_sit_key"], label_visibility="collapsed")
        audio_sit = audio_recorder("", key=st.session_state['audi_sit_key'], pause_threshold=-1.)
        transcript_sit, audio_sit_path = transcribe(audio_sit, f"situation_audio.mp3")
        if transcript_sit != "":
            # print("test")
            st.session_state["text_sit"] = transcript_sit
    with a1:
        st.text_area("ситуацията", key="text_sit", placeholder="write here", height=257, label_visibility="collapsed")

    "  "
    "#### **Опишете устно или писмено Вашата реакция:**"
    "(за гласов запис натиснете микрофона)"
    b1, b2 = st.columns([7, 1])
    with b2:
        #with stylable_container(
        #    key="orange",
        #    css_styles="""
        #        button {
        #            background-color: green;
        #            color: white;
        #            border-radius: 20px;
        #        }
        #        """,
        #): 
        #    audio_act = st.audio_input("действия", key=st.session_state["audi_act_key"], label_visibility="collapsed")
        audio_act = audio_recorder("", key=st.session_state['audi_act_key'])
        transcript_act, audio_act_path = transcribe(audio_act, f"action_audio.mp3")
        if transcript_act != "":
            st.session_state["text_act"] = transcript_act
    with b1:
        st.text_area("реакцията", key="text_act", height=257, label_visibility="collapsed")

    "#### Опишете устно или писмено **ефекта** от Вашата реакция:"
    "(за гласов запис натиснете микрофона)",
    c1, c2 = st.columns([7, 1])
    with c2:
        #'''
        #with stylable_container(
        #    key="orange",
        #    css_styles="""
        #        button {
        #            background-color: green;
        #            color: white;
        #            border-radius: 20px;
        #        }
        #        """,
        #): 
        #    audio_eff = st.audio_input("как се е развила ситуацията", key=st.session_state["audi_eff_key"], label_visibility="collapsed")
        #'''
        audio_eff = audio_recorder("", key=st.session_state['audi_eff_key'])
        transcript_eff, audio_eff_path = transcribe(audio_eff, f"effect_audio.mp3")
        if transcript_eff != "":
            st.session_state["text_eff"] = transcript_eff
    with c1:
        st.text_area("Опишете ефекта от вашата реакция:", key="text_eff", height=257, label_visibility="collapsed")

    st.markdown("#### Оценете ефекта от Вашата реакция:")
    #e1, e2 = st.columns([5, 1])
    #with e1:
    #    st.markdown("#### Оценете ефекта от вашата реакция от 1 до 10:")
    #with e2:
    #    st.info("инфо")
    
    explain_grades = """# скала за оценяване:

    1: влоши ситуацията
    2: неефективна
    3: слабо ефективна
    4: ефективна
    5: много ефективна
    """
    #st.slider("(за повече информация натиснете въпросителния знак) ", 1, 5, key="slider", help=explain_grades, label_visibility="visible")
    grades=[1, 2, 3, 4, 5]

    def grade_to_label(g):
        labels = ("лоша реакция", "неефективна реакция", "слабо ефективна реакция", "ефективна реакция", "много ефективна реакция")
        return labels[g - 1]

    grade = st.radio("?", grades, key="grade", format_func=grade_to_label, index=None, label_visibility="collapsed")


    st.markdown("#### Състояние на детето")

    if s is not None:

        f1, f2, f3 = st.columns(3)

        with f1:
            st.checkbox("Аутизъм (МКБ:ььь)", key="autism")
            st.checkbox("нз2", key="ns2")
            st.checkbox("нз5", key="ns5")
            st.checkbox("нз8", key="ns8")
            st.checkbox("нз11", key="ns11")

        with f2:
            st.checkbox("Дислексия (МКБ:ььь)", key="dislexia")
            st.checkbox("нз3", key="ns3")
            st.checkbox("нз6", key="ns6")
            st.checkbox("нз9", key="ns9")
            st.checkbox("нз12", key="ns12")

        with f3:
            st.checkbox("нз1", key="ns1")
            st.checkbox("нз4", key="ns4")
            st.checkbox("нз7", key="ns7")
            st.checkbox("нз10", key="ns10")


        st.markdown("#### Линкът към картата за функционална оценка на детето:")
        st.markdown("###### При нова версия ви молим за доставка")
        #st.text_input("профилът", key="ti_profile", label_visibility="collapsed")
        st.link_button(st.session_state['profile_filename'], st.session_state['ti_profile'])

        st.markdown(" ")

        submit = st.button("подаване на формуляр", type="primary", use_container_width=True)

        if not "balloons" in st.session_state:
            st.session_state.balloons = False

        if st.session_state.balloons:
            
            st.balloons()
            st.toast("Формулярът е изпратен", icon='🥳') 

            st.session_state.balloons = False

        if submit:
            def check_filled():
                if st.session_state['sid'] is None:
                    return False
                if st.session_state['ti_xp_toghether'] == "":
                    return False
                if st.session_state['text_sit'] == "":
                    return False
                if st.session_state['text_act'] == "":
                    return False
                if st.session_state['text_eff'] == "":
                    return False
                if st.session_state['grade'] == None:
                    return False
                return True

            if check_filled():

                st.session_state.download = True
                st.session_state.balloons = True

                update = not (new_student_pr == student_pr)
                print(update)

                inputs_exel = {
                    "teacher_id": teacher_id,
                    "student_id": st.session_state["sid"],
                    "date": date.strftime("%d-%m-%Y"),
                    "teacher_xp": teacher_xp,
                    "student_age": student_pr['age'],
                    "xp_with_child": st.session_state["ti_xp_toghether"],
                    "student_profile": st.session_state["ti_profile"],
                    "situation": st.session_state["text_sit"],
                    "action": st.session_state["text_act"],
                    "effect": st.session_state["text_eff"],
                    "grade": st.session_state['grade']
                }

                inputs_ = {
                    "kid_profile": student_pr,
                    "situation": st.session_state["text_sit"],
                    "action": st.session_state["text_act"],
                    "effect": st.session_state["text_eff"],
                    "grade": st.session_state['grade']
                }

                exel = parser.create_exel(inputs_exel)
                parser.save_scenario()
                if not exel is None:
                    st.session_state.balloons = True
                st.session_state.exel = exel
                # print(st.session_state.exel)
                time = now.strftime('%H:%M')

                parser.add_form_to_db(teacher_id, audio_sit_path, audio_act_path, audio_eff_path, 
                                        transcript_sit, transcript_act, transcript_eff, st.session_state["sid"])

                st.rerun()
            else:
                st.toast("Има още празни полета", icon="❗")
    else:
        st.warning("Моля изберете ученик")
        
        


elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
