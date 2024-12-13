import streamlit as st
import datetime
import form_parser
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_extras.stylable_container import stylable_container
import os
from streamlit_extras.bottom_container import bottom
from st_audiorec import st_audiorec
import gdown
from bs4 import BeautifulSoup

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

print(student_ids)

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

def extract_file_name_from_html(url):
    output = 'test.html'
    global parser
    parser.download(url, output)

    try:
        with open(output, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')

        # Find the <meta> tag with property "og:title"
        meta_tag = soup.find('meta', property='og:title')

        if meta_tag and 'content' in meta_tag.attrs:
            return meta_tag['content']

        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@st.cache_resource
def get_student_data(id):
    global parser
    students = parser.students
    print(students)
    student = students.loc[students['Идентификационен номер'] == str(id)]
    print(student)
    if not student.empty:
        url = str(student['линк към файл с профил'].values[0])
        print(url)
        st.session_state['ti_profile'] = url
        file = parser.get_filename(url)
        if file == None:
            file = "link"
        st.session_state['profile_filename'] = file

        autism = bool(int(student['аутизъм'].values[0]))
        dislexia = bool(int(student['дислекция'].values[0]))
        ns1 = bool(int(student['нз1'].values[0]))
        ns2 = bool(int(student['нз2'].values[0]))
        ns3 = bool(int(student['нз3'].values[0]))
        ns4 = bool(int(student['нз4'].values[0])) 
        ns5 = bool(int(student['нз5'].values[0])) 
        ns6 = bool(int(student['нз6'].values[0])) 
        ns7 = bool(int(student['нз7'].values[0])) 
        ns8 = bool(int(student['нз8'].values[0])) 
        ns9 = bool(int(student['нз9'].values[0]))        
        ns10 = bool(int(student['нз10'].values[0])) 
        ns11 = bool(int(student['нз11'].values[0]))
        ns12 = bool(int(student['нз12'].values[0])) 

        st.session_state['autism'] = autism
        st.session_state['dislexia'] = dislexia
        st.session_state['ns1'] = ns1
        st.session_state['ns2'] = ns2
        st.session_state['ns3'] = ns3
        st.session_state['ns4'] = ns4
        st.session_state['ns5'] = ns5
        st.session_state['ns6'] = ns6
        st.session_state['ns7'] = ns7
        st.session_state['ns8'] = ns8
        st.session_state['ns9'] = ns9     
        st.session_state['ns10'] = ns10
        st.session_state['ns11'] = ns11
        st.session_state['ns12'] = ns12

        student_profile = [url, autism, dislexia, ns1, ns2, ns3, ns4, ns5, ns6, ns7, ns8, ns9, ns10, ns11, ns12]
    else:
        st.warning("Did not find the student in the database")
        return None

    return student_profile, file

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
    #st.markdown("## Идентификационна информация\n\n ##### Вашият уникален анонимен идентификатор:")
    #st.text_input("a", key="tid", label_visibility="collapsed")
    #if st.session_state["tid"] != "" and int(st.session_state["tid"]) != logged_teacher_id:
    #    teacher_form = get_teacher_data(id=st.session_state["tid"])

    st.markdown("##### Уникален анонимен номер на детето:")
    student = st.selectbox("b", student_ids, key="sid", label_visibility="collapsed", index=None)
    
    if st.session_state["sid"]:
        student_pr, file = get_student_data(int(student))
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
    a1, a2 = st.columns([5, 1])

    with a2:
        with stylable_container(
            key="orange",
            css_styles="""
                button {
                    background-color: green;
                    color: white;
                    border-radius: 20px;
                }
                """,
        ):  
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
        with stylable_container(
            key="orange",
            css_styles="""
                button {
                    background-color: green;
                    color: white;
                    border-radius: 20px;
                }
                """,
        ): 
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
        with stylable_container(
            key="orange",
            css_styles="""
                button {
                    background-color: green;
                    color: white;
                    border-radius: 20px;
                }
                """,
        ): 
            audio_eff = st.audio_input("как се е развила ситуацията", key=st.session_state["audi_eff_key"], label_visibility="collapsed")
        transcript_eff, audio_eff_path = transcribe(audio_eff, f"effect_audio_{today}.mp3")
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

    grade = st.radio(
        "How would you like to be contacted?", grades, format_func=grade_to_label, index=None, label_visibility="collapsed")


    st.markdown("#### Състояние на детето")

    if not st.session_state['ti_profile'] == "":

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


        st.markdown("#### Какъв е линкът към картата за функционална оценка на детето:")
        #st.text_input("профилът", key="ti_profile", label_visibility="collapsed")
        st.link_button(st.session_state['profile_filename'], st.session_state['ti_profile'])

        st.markdown(" ")

        submit = st.button("подаване на формуляр", type="primary", use_container_width=True)

        if not "ballons" in st.session_state:
            st.session_state.balloons = False

        if st.session_state.balloons:
            st.session_state.balloons = False
            st.balloons()
            st.toast("Формулярът е изпратен", icon='🥳') 

        wav_audio = st_audiorec()

        if wav_audio is not None:
            st.audio(wav_audio, format="audio/wav")

        if submit:
            st.session_state.download = True
            st.session_state.balloons = True

            update = not new_student_pr == student_pr
            print(update)

            inputs = {
                "teacher_id": teacher_id,
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

            if transcript_sit == "":
                transcript_sit = "empty"
            if transcript_act == "":
                transcript_act = "empty"
            if transcript_eff == "":
                transcript_eff = "empty"

            parser.add_from_to_db(exel_path, teacher_id, audio_sit_path, audio_act_path, audio_eff_path, 
                                    transcript_sit, transcript_act, transcript_eff, st.session_state["ti_student_id"], date.strftime("%d-%m-%Y"), time)

            st.rerun()
    else:
        st.warning("Моля изберете ученик")
        


elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
