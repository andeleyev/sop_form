import streamlit as st
import datetime
import form_parser
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from audio_recorder_streamlit import audio_recorder
import pandas as pd 
import time

st.set_page_config(page_title="SOP Form Parser", page_icon="🗣️", layout="centered", initial_sidebar_state="auto", menu_items=None)

api = st.secrets["general"]["api_key"]


now = datetime.datetime.now()
today = now.strftime("%d-%m-%Y")

@st.cache_resource
def initialize(key):
    os.environ["OPENAI_API_KEY"] = key
    parser = form_parser.Parser()
    return parser

parser = initialize(api)

ALLOWED_DOCUMENT_TYPES = ['.docx', '.doc', '.odt', '.ott', '.rtf', '.pages', '.txt', '.pdf', '.sxw', '.wpd']

student_ids = [999, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014]

instruct_sit = """Насочващи въпроси:
- Каква беше конкретната обстановка?
- Кои бяха участниците в ситуацията?
- Какво предизвика ситуацията?
- Как реагира ученика със СОП?
"""

instruct_act = """Насочващи въпроси:
- Каква беше Вашата реакция при възникването на ситуацията?
- Какви действия предприехте за да справите със ситуацията?
- Бяха ли предприети мерки за такива ситуации?
"""

instruct_eff = """Насочващи въпроси:
- Как се е разрешила ситуацията и как реагира ученика?
- Успяхте ли да овладеете ситуацията преди да ескалира?
- Имаше ли неочаквани резултати или предизвикателства?
"""

# @st.cache_data
def get_teacher_data(username):
    global parser
    teachers = parser.teachers

    teacher = teachers.loc[teachers['username'] == username]
    # print("Teacher: ", teacher)

    if not teacher.empty:
        teacher_since = teacher['Ресурсен учител от година'].values[0]
        if teacher_since.isdigit():
            diff = now.year - int(teacher_since)
            teacher_xp = f"{diff} до {diff + 1}"
        else:
            teacher_xp = ""
        
        teacher_id = teacher['Идентификационен номер на учител'].values[0]
    else:
        st.warning("Did not find the teacher in the database")
        return None

    return teacher_id, teacher_xp, 

# @st.cache_data
def get_student_data(id):
    global parser
    students_all = parser.students
    # print(students)
    students = students_all.loc[students_all['id student'] == str(id)].copy()

    students['date of entry'] = pd.to_datetime(students['date of entry'], format='%d-%m-%Y %H:%M', errors='coerce')
    students = students.dropna(subset=['date of entry'])
    students_sorted = students.sort_values('date of entry', ascending=False)

    if not students_sorted.empty:
        student = students_sorted.iloc[0]
        # print(student['date of entry'])

        sp_dict = dict(zip(
            students.columns.tolist(),
            student.tolist()
        ))

        sp_dict['age'] =student['age']
        sp_dict['link functional card'] = str(student['link functional card'])

        file = parser.get_filename(sp_dict['link functional card'])

        if file == None:
            sp_dict['link functional card'] = ""

        #print("file: ", file)
        sp_dict.pop('id teacher')
    else:
        return dict(), None

    return sp_dict, file

@st.cache_data
def transcribe(audio, audio_path, keey):
    if not audio:
        return "", "None"

    global parser

    with open(audio_path, "wb") as file:
        print("saving audio: ", audio_path)
        file.write(audio)

    script = parser.transcript_speech(audio_path)
    st.session_state[keey] = script
    
    return script, audio_path


# =====================================================================
#       Defining State Variables
# =====================================================================

if "Complex needs" not in st.session_state:
    st.session_state['Complex needs'] = ""

if not "counter" in st.session_state:
    st.session_state['counter'] = 0

if not "download" in st.session_state:
    st.session_state['download'] = False

if not "ti_age" in st.session_state:
    st.session_state['ti_age'] = ""
if not "ra_gender" in st.session_state:
    st.session_state['ra_gender'] = None

if "profile_filename" not in st.session_state:
    st.session_state['profile_filename'] = ""
if "link_profile" not in st.session_state:
    st.session_state['link_profile'] = ""

if "audi_sit_keys" not in st.session_state:
    st.session_state['audi_sit_key'] = "sit" + str(st.session_state['counter'])
if "audi_act_key" not in st.session_state:
    st.session_state['audi_act_key'] = "act" + str(st.session_state['counter'])
if "audi_eff_key" not in st.session_state:
    st.session_state['audi_eff_key'] = "eff" + str(st.session_state['counter'])
if "text_sit" not in st.session_state:
    st.session_state['text_sit'] = ""
if "text_act" not in st.session_state:
    st.session_state['text_act'] = ""
if "text_eff" not in st.session_state:
    st.session_state['text_eff'] = ""

def reset_state_student():
    print("Setting student information to empty")
    st.session_state['link_profile'] = ""
    st.session_state['profile_filename'] = file

    st.session_state['ra_gender'] = None
    st.session_state['ti_age'] =""

    st.session_state['Autism Spectrum Disorder'] = False
    st.session_state['Speech and language disorders'] = False
    st.session_state['Dyslexia'] = False
    st.session_state['Dyscalculia'] = False
    st.session_state['Dyspraxia'] = False
    st.session_state['Moderate to severe learning difficulties'] = False
    st.session_state['ADHD'] = False
    st.session_state['Attachement disorder'] = False 
    st.session_state['Anxiety disorders'] = False
    st.session_state['Hearing impairment'] = False
    st.session_state['Visual impairment'] = False
    st.session_state['Sensory processing disorder'] = False
    st.session_state['Epilepsy'] = False

    st.session_state['Physical disabilities'] = ""
    st.session_state['Chronic health conditions'] = ""
    st.session_state['Genetic conditions'] = ""
    st.session_state['Complex needs'] = ""

    st.session_state['has physical'] = st.session_state['Physical disabilities'] != ""
    st.session_state['has chronic'] = st.session_state['Chronic health conditions'] != ""
    st.session_state['has genetic'] = st.session_state['Genetic conditions'] != ""
    st.session_state['has complex'] = st.session_state['Complex needs'] != "" 

    st.session_state['ti_xp_together'] = ""    

def reset_state_scenario():
    print("resetting !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    st.session_state['counter'] += 1
    st.session_state['audi_eff_key'] = "eff" + str(st.session_state['counter'])
    st.session_state['audi_act_key'] = "act" + str(st.session_state['counter'])
    st.session_state['audi_sit_key'] = "sit" + str(st.session_state['counter'])

    st.session_state['sid'] = None

    st.session_state['text_sit'] = ""
    st.session_state['text_act'] = ""
    st.session_state['text_eff'] = ""

    st.session_state['ra_gender'] = None
    st.session_state['ti_age'] = ""
    st.session_state['link_profile'] = ""

    st.session_state['audi_sit'] = ""
    st.session_state['audi_act'] = ""
    st.session_state['audi_eff'] = ""

# ======================================================================
#           Start of the Application
# ======================================================================

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

authenticator.login(fields={'Form name':'СОП Проект - Вход', 'Username':'Потребителско име:', 'Password':'Парола:', 'Login':'Влез'})

if st.session_state['authentication_status']:

    k1, k2 = st.columns([3, 1])
    with k1:
        username = st.session_state['username']
        teacher_id, teacher_xp = get_teacher_data(username)  
        st.write(f'Добре дошли *{st.session_state['name']}* ')
        st.write(f"Вашият Идентификатор: {teacher_id}")
    with k2:
        authenticator.logout("Изход")



    
    if st.session_state['download']:
        # Page after filling out the form

        st.success("Формулярът е изпратен успешно")
        if st.session_state['balloons']:
            st.balloons()
            st.session_state['balloons'] = False
        # st.toast("Формулярът е изпратен", icon='🥳') 
        d1, d2 = st.columns(2)
        with d1:
            downloaded = st.download_button("изтегляне на попълнения формуляр", type="primary", use_container_width=True, data=st.session_state['exel'], file_name="filled_form.xlsx")
        with d2:
            reset = st.button("попълни нов формулар", type="primary", use_container_width=True)

        if reset:
            parser.reload()
            st.session_state['download'] = False
            reset_state_scenario()
            reset_state_student()
            st.cache_data.clear()
            st.rerun()

    else:
        # From Here: Page of the actual form
        st.markdown('# СОП - Формуляр \n\n')

        def update_student():
            sid = st.session_state['sid']

            if sid is None:
                print("No student --")
                return
            sp, file = get_student_data(sid)

            if not bool(sp):
                st.toast("first form for this student")
                reset_state_student()
            else:
                print("Loading Student: ", sp['id student'])
                st.session_state['link_profile'] = sp['link functional card']
                st.session_state['profile_filename'] = file

                st.session_state['ra_gender'] = str(sp['gender'])
                st.session_state['ti_age'] = str(sp['age'])

                # Session State Proxy's NEED to be names exactly as the columns of the dataframe/google-sheets
                st.session_state['Autism Spectrum Disorder'] = bool(int(sp['Autism Spectrum Disorder']))
                st.session_state['Speech and language disorders'] = bool(int(sp['Speech and language disorders']))
                st.session_state['Dyslexia'] = bool(int(sp['Dyslexia']))
                st.session_state['Dyscalculia'] = bool(int(sp['Dyscalculia']))
                st.session_state['Dyspraxia'] = bool(int(sp['Dyspraxia'])) 
                st.session_state['Moderate to severe learning difficulties'] = bool(int(sp['Moderate to severe learning difficulties'])) 
                st.session_state['ADHD'] = bool(int(sp['ADHD'])) 
                st.session_state['Attachement disorder'] = bool(int(sp['Attachement disorder'])) 
                st.session_state['Anxiety disorders'] = bool(int(sp['Anxiety disorders'])) 
                st.session_state['Hearing impairment'] = bool(int(sp['Hearing impairment']))
                st.session_state['Visual impairment'] = bool(int(sp['Visual impairment']))  
                st.session_state['Sensory processing disorder'] = bool(int(sp['Sensory processing disorder']))
                st.session_state['Epilepsy'] = bool(int(sp['Epilepsy']))

                st.session_state['Physical disabilities'] = str(sp['Physical disabilities'])
                st.session_state['Chronic health conditions'] = str(sp['Chronic health conditions'])
                st.session_state['Genetic conditions'] = str(sp['Genetic conditions'])
                st.session_state['Complex needs'] = str(sp['Complex needs'])

                st.session_state['has physical'] = st.session_state['Physical disabilities'] != ""
                st.session_state['has chronic'] = st.session_state['Chronic health conditions'] != ""
                st.session_state['has genetic'] = st.session_state['Genetic conditions'] != ""
                st.session_state['has complex'] = st.session_state['Complex needs'] != ""

                if file == "link":
                    st.toast("The URL to the student card could not be loaded correctly", icon="❗")

            xp = parser.get_xp_together(sid, teacher_id)
            if xp is not None:
                st.session_state['ti_xp_together'] = xp
            else:
                st.session_state['ti_xp_together'] = ""

        st.markdown("##### :red[*] Уникален анонимен номер на ученика:")
        st.selectbox("b", student_ids, key="sid", label_visibility="collapsed", index=None, on_change=update_student)

        st.markdown("#### :red[*] От колко години работите с този ученик:")
        st.text_input("От колко години работите с този ученик:", key="ti_xp_together", label_visibility="collapsed")

        # ====================================================================================================
        #           Situation and Reaction
        # ====================================================================================================

        st.markdown("\n\n")
        st.markdown("\n\n")
        st.markdown("## Ситуация и реакция" )
        st.markdown("При попълване моля, :red[не] използвайте истинското име на ученика")
        st.markdown("##### :red[*] Дата на :red[случката]:")   
        date = st.date_input("Дата", format="DD.MM.YYYY", label_visibility="collapsed") # remove default to make it today

        st.markdown(" ")
        st.markdown("#### :red[*] Опишете устно или писмено :blue[Ситуацията], която се е случила:")
        st.markdown("(за гласов запис натиснете микрофона)")
        a1, a2 = st.columns([7, 1])
        with a2:
            audio_sit = audio_recorder("", key=st.session_state['audi_sit_key'], pause_threshold=30.)
            transcript_sit, audio_sit_path = transcribe(audio_sit, f"situation_audio.mp3", "text_sit")

        with a1:
            st.text_area("ситуацията", key="text_sit", placeholder=instruct_sit, height=257, label_visibility="collapsed")
        
        st.markdown("  ")
        st.markdown("#### :red[*] Опишете устно или писмено Вашата :blue[Реакция]:")
        st.markdown("(за гласов запис натиснете микрофона)")
        b1, b2 = st.columns([7, 1])
        with b2:
            audio_act = audio_recorder("", key=st.session_state['audi_act_key'], pause_threshold=30.)
            transcript_act, audio_act_path = transcribe(audio_act, f"action_audio.mp3", "text_act")
        with b1:
            st.text_area("реакцията", key="text_act", placeholder=instruct_act, height=257, label_visibility="collapsed")

        st.markdown("#### Опишете устно или писмено :blue[Ефекта] от Вашата реакция:")
        st.markdown("(за гласов запис натиснете микрофона)")
        c1, c2 = st.columns([7, 1])
        with c2:
            audio_eff = audio_recorder("", key=st.session_state['audi_eff_key'], pause_threshold=30.)
            transcript_eff, audio_eff_path = transcribe(audio_eff, f"effect_audio.mp3", "text_eff")
        with c1:
            st.text_area("Опишете ефекта от вашата реакция:", placeholder=instruct_eff, key="text_eff", height=257, label_visibility="collapsed")


        st.markdown("#### :red[*] Оценете ефекта от Вашата реакция:")
        grades=[1, 2, 3, 4, 5]

        def grade_to_label(g):
            labels = ("лоша реакция", "неефективна реакция", "слабо ефективна реакция", "ефективна реакция", "много ефективна реакция")
            return labels[g - 1]

        grade = st.radio("?", grades, format_func=grade_to_label, index=None, label_visibility="collapsed")
    
        # =========================================================================
        #           Student Profile
        # =========================================================================

        st.markdown("\n\n")
        st.markdown("\n\n")

        st.markdown("## Профил на ученика")

        if st.session_state['sid'] is not None:

            st.markdown("#### :red[*] На колко години е ученикът?")
            st.text_input("age", key='ti_age', label_visibility="collapsed")

            st.markdown("#### :red[*] Пол")
            st.radio("g", ("мъж", "жена"), horizontal=True, key='ra_gender', label_visibility="collapsed")

            st.markdown("#### Състояние на ученика")

            st.markdown("###### 1. Проблеми с комуникация и взаимодействие")

            c1, c2 = st.columns(2)

            with c1:
                st.checkbox("Разстройство от аутистичния спектър (МКБ F84)", key="Autism Spectrum Disorder")
            with c2:
                st.checkbox("Разстройства на речта и езика (МКБ F80)", key="Speech and language disorders")


            st.markdown("###### 2. Нужди от когниция и учене")

            c1, c2 = st.columns(2)

            with c1:
                st.checkbox("Дислексия (МКБ F81.0)", key="Dyslexia")
                st.checkbox("Диспраксия (МКБ F82)", key="Dyspraxia")
            with c2:
                st.checkbox("Дискалкулия (МКБ F81.2)", key="Dyscalculia")
                st.checkbox("Умерени до тежки обучителни трудности (МКБ F79)", key="Moderate to severe learning difficulties")


            st.markdown("###### 3. Cоциално, емоционално и психично здраве")

            c1, c2 = st.columns(2)

            with c1:
                st.checkbox("Хиперкинетично разстройство с нарушение на вниманието (МКБ F90)", key="ADHD")
                st.checkbox("Панически разстройства (МКБ F41)", key="Anxiety disorders")
                st.checkbox("Слепота и намалено зрение (МКБ H54)", key="Visual impairment")
            with c2:
                st.checkbox("Разстройство на реактивността на привързаността (МКБ F94.1)", key="Attachement disorder")
                st.checkbox("Слухово увреждане (МКБ H90)", key="Hearing impairment")


            st.markdown("###### 4. Сензорни и/или физически нужди")

            c1, c2 = st.columns(2)

            with c1:
                st.checkbox("Разстройство на сензорната интеграция (МКБ F88)", key="Sensory processing disorder")
            with c2:
                if st.checkbox("Физически увреждания", key="has physical"):
                    if "physical_value" not in st.session_state:
                        st.session_state['physical_value'] = st.session_state['Physical disabilities']
                    st.text_input("physical", key="physical_value", label_visibility="collapsed", placeholder="Опишете тук физическите увреждания")
                    st.session_state['Physical disabilities'] = st.session_state['physical_value']

            st.markdown("###### 5. Медицински или неврологични нужди")

            c1, c2 = st.columns(2)
            
            with c1:
                st.checkbox("Епилепсия (МКБ G40)", key="Epilepsy")

                if st.checkbox("Генетични състояния", key="has genetic"):
                    if "gentic_value" not in st.session_state:
                        st.session_state['gentic_value'] = st.session_state['Genetic conditions']
                    st.text_input("genetic", key="gentic_value", label_visibility="collapsed", placeholder="Опишете тук генетичното състояние")
                    st.session_state['Genetic conditions'] = st.session_state['gentic_value']
            with c2:
                if st.checkbox("Хронични здравословни състояния", key="has chronic"):
                    if "chonic_value" not in st.session_state:
                        st.session_state['chonic_value'] = st.session_state['Chronic health conditions']
                    st.text_input("chronic", key="chonic_value",  label_visibility="collapsed", placeholder="Опишете тук състояниеto")
                    st.session_state['Chronic health conditions'] = st.session_state['chonic_value']

                if st.checkbox("Комплексни нужди", key="has complex"):
                    if "complex_value" not in st.session_state:
                        st.session_state['complex_value'] = st.session_state['Complex needs']
                    st.text_input("needs", key="complex_value", label_visibility="collapsed", placeholder="Опишете тук нуждите")
                    st.session_state['Complex needs'] = st.session_state['complex_value']

            if st.session_state['link_profile'] == "":

                
                st.markdown("#### За този ученик няма подадена карта функтионална оценка - Подадете я тук (Опционално)")
                karta = st.file_uploader("Functional Card (Optional)", ALLOWED_DOCUMENT_TYPES, label_visibility="collapsed")
            else:
                st.markdown("#### Картата функционална оценка на ученика:")
                
                #st.text_input("профилът", key="link_profile", label_visibility="collapsed")
                t1, t2 = st.columns(2)
                with t1: 
                    st.markdown("###### Линк към картата")
                    st.link_button(st.session_state['profile_filename'], st.session_state['link_profile'], use_container_width=True)
                with t2:
                    st.markdown("###### При нова карта тук (Опционално)")
                    karta = st.file_uploader("При нова карта подате тук (Опционално)", label_visibility="collapsed")      

            st.markdown(" ")

            # =============================================================
            #           On Form Submit
            # =============================================================

            submit = st.button("подаване на формуляр", type="primary", use_container_width=True)

            if submit:
                def check_filled():
                    if st.session_state['sid'] is None:
                        return False
                    if st.session_state['ti_xp_together'] == "":
                        return False
                    if st.session_state['text_sit'] == "":
                        return False
                    if st.session_state['text_act'] == "":
                        return False
                    if st.session_state['ti_age'] == "":
                        return False
                    if st.session_state['ra_gender'] is None:
                        return False
                    if grade == None:
                        return False

                    return True

                if check_filled():

                    def upload_card(card):
                        if card is None:
                            return

                        with open(card.name, 'wb') as f:
                            f.write(card.getbuffer())
                        
                        file_id = parser.karta_to_drive(card.name)
                        
                        if file_id:
                            st.toast('File uploaded successfully!')
                            link = parser.create_google_drive_link(file_id)
                            st.session_state['link_profile'] = link
                            st.session_state['profile_filename'] = parser.get_filename(link)
                            print("Saved card with id: ", file_id)  

                        os.remove(card.name)

                    if karta:
                        upload_card(karta)

                    # Creating a new student Profile dict and updating it according to the form - Check for changes in the Student profile
                    old_student_pr, _ = get_student_data(st.session_state['sid'])
                    new_student_pr = old_student_pr.copy()

                    # print(old_student_pr, "\n\n", new_student_pr)

                    profile_tags = ["Autism Spectrum Disorder", "Speech and language disorders", "Dyslexia", "Dyscalculia", "Dyspraxia", "Moderate to severe learning difficulties",
                                    "ADHD", "Attachement disorder", "Anxiety disorders", "Hearing impairment", "Visual impairment", "Sensory processing disorder", "Epilepsy"]
                    profile_ti_fiels = ["Physical disabilities", "Chronic health conditions", "Genetic conditions", "Complex needs"]

                    for tag in profile_tags:
                        new_student_pr[tag] = str(int(st.session_state[tag]))

                    if st.session_state['has physical']:
                        if st.session_state['Physical disabilities'] == "":
                            new_student_pr['Physical disabilities'] = "неуточнено"
                        else:
                            new_student_pr['Physical disabilities'] = st.session_state['Physical disabilities']
                    else:
                        new_student_pr['Physical disabilities'] = ""

                    if st.session_state['has chronic']:
                        if st.session_state['Chronic health conditions'] == "":
                            new_student_pr['Chronic health conditions'] = "неуточнено"
                        else:
                            new_student_pr['Chronic health conditions'] = st.session_state['Chronic health conditions']
                    else:
                        new_student_pr['Chronic health conditions'] = ""

                    if st.session_state['has genetic']:
                        if st.session_state['Genetic conditions'] == "":
                            new_student_pr['Genetic conditions'] = "неуточнено"
                        else:
                            new_student_pr['Genetic conditions'] = st.session_state['Genetic conditions']
                    else:
                        new_student_pr['Genetic conditions'] = ""

                    if st.session_state['has complex']:
                        if st.session_state['Complex needs'] == "":
                            new_student_pr['Complex needs'] = "неуточнено"
                        else:
                            new_student_pr['Complex needs'] = st.session_state['Complex needs']
                    else:
                        new_student_pr['Complex needs'] = ""

                    new_student_pr['age'] = st.session_state['ti_age']
                    new_student_pr['gender'] = st.session_state['ra_gender']
                    new_student_pr['link functional card'] = st.session_state['link_profile']

                    update = not (new_student_pr == old_student_pr)

                    if update:
                        st.toast("Updating the database of students with new row")
                        parser.add_student_to_db(new_student_pr, teacher_id, st.session_state['sid'])

                    grade_text = grade_to_label(grade)

                    inputs_exel = {
                        "teacher_id": teacher_id,
                        "student_id": st.session_state['sid'],
                        "date": date.strftime('%d-%m-%Y'),
                        "teacher_xp": teacher_xp,
                        "student_age": st.session_state['ti_age'],
                        "xp_with_child": st.session_state['ti_xp_together'],
                        "student_profile": st.session_state['link_profile'],
                        "situation": st.session_state['text_sit'],
                        "action": st.session_state['text_act'],
                        "effect": st.session_state['text_eff'],
                        "grade": grade_text
                    }


                    new_pr = [label for label in profile_tags if bool(int(new_student_pr[label]))]     
                    new_pr += [label + ": " + new_student_pr[label] for label in profile_ti_fiels if new_student_pr[label] != ""]               

                    student_pr = {
                        "age": st.session_state['ti_age'],
                        "gender": st.session_state['ra_gender'],
                        "diagnosis": new_pr
                    }

                    inputs_form = {
                        "student_profile": student_pr,
                        "date": date.strftime('%d-%m-%Y'),
                        "situation": st.session_state['text_sit'],
                        "action": st.session_state['text_act'],
                        "effect": st.session_state['text_eff'],
                        "grade": grade
                    }

                    exel = parser.create_exel(inputs_exel)
                    st.session_state['exel'] = exel

                    try:
                        id_drive = parser.add_form_to_db(inputs_form, teacher_id, audio_sit_path, audio_act_path, audio_eff_path, 
                                            transcript_sit, transcript_act, transcript_eff, st.session_state['sid'], st.session_state['ti_xp_together'])
                    except Exception as e:
                        st.error("Имаше Проблем при испращането на формуляра! Моля изчакаите докато се опитваме отново.")
                        st.error(e)
                        time.sleep(150)
                        try:
                            id_drive = parser.add_form_to_db(inputs_form, teacher_id, audio_sit_path, audio_act_path, audio_eff_path, 
                                            transcript_sit, transcript_act, transcript_eff, st.session_state['sid'], st.session_state['ti_xp_together'])
                        except Exception as e:
                            st.error("При втори опит пак не стана. Моля заредете отново или се опитаите в по късен момент пак")
                            st.error(e)

                    if id_drive and exel:
                        st.session_state['balloons'] = True
                        st.session_state['download'] = True
                    st.rerun()
                else:
                    st.toast("Има още празни полета", icon="❗")
        else:
            st.warning("Моля изберете ученик")
            
        
elif st.session_state['authentication_status'] is False:
    st.error('Потребителското име/паролата е неправилно')

elif st.session_state['authentication_status'] is None:
    st.warning('Моля, въведете вашето потребителско име и парола')
