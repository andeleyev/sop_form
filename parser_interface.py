import streamlit as st
import datetime
import form_parser
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from audio_recorder_streamlit import audio_recorder

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

# @st.cache_data
def get_teacher_data(username):
    global parser
    teachers = parser.teachers

    teacher = teachers.loc[teachers['username'] == username]
    # print("Teacher: ", teacher)

    if not teacher.empty:
        diff = now.year - int(teacher['Ресурсен учител от година'].values[0])
        teacher_xp = f"{diff}-{diff + 1}"
        teacher_id = teacher['Идентификационен номер на учител'].values[0]
    else:
        st.warning("Did not find the teacher in the database")
        return None

    return teacher_id, teacher_xp, 

# @st.cache_data
def get_student_data(id):
    global parser
    students= parser.students
    # print(students)
    students = students.loc[students['id student'] == str(id)]
    students_sorted = students.sort_values('date of entry', ascending=False)

    if not students_sorted.empty:
        student = students_sorted.iloc[0]

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

    st.session_state['autism'] = False
    st.session_state['dyslexia'] = False
    st.session_state['ns1'] = False
    st.session_state['ns2'] = False
    st.session_state['ns3'] = False
    st.session_state['ns4'] = False
    st.session_state['ns5'] = False
    st.session_state['ns6'] = False
    st.session_state['ns7'] = False
    st.session_state['ns8'] = False
    st.session_state['ns9'] = False
    st.session_state['ns10'] = False
    st.session_state['ns11'] = False
    st.session_state['ns12'] = False   

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

authenticator.login(fields={'Form name':'Login', 'Username':'вашето потребителско име', 'Password':'парола', 'Login':'Login', 'Captcha':'Captcha'})

if st.session_state['authentication_status']:

    k1, k2 = st.columns([3, 1])
    with k1:
        username = st.session_state['username']
        teacher_id, teacher_xp = get_teacher_data(username)  
        st.write(f'Добре дошли *{st.session_state['name']}* ')
        st.write(f"Вашият Идентификатор: {teacher_id}")
    with k2:
        authenticator.logout()



    
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

            
            st.session_state['download'] = False
            reset_state_scenario()
            reset_state_student()
            st.cache_data.clear()
            st.rerun()

    else:
        # From Here: Page of the actual form
        st.markdown('# Бланка за описване на ситуация и реакция при работа с деца със СОП \n\n')

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

                st.session_state['autism'] = bool(int(sp['autism']))
                st.session_state['dyslexia'] = bool(int(sp['dyslexia']))
                st.session_state['ns1'] = bool(int(sp['ns1']))
                st.session_state['ns2'] = bool(int(sp['ns2']))
                st.session_state['ns3'] = bool(int(sp['ns3'])) 
                st.session_state['ns4'] = bool(int(sp['ns4'])) 
                st.session_state['ns5'] = bool(int(sp['ns5'])) 
                st.session_state['ns6'] = bool(int(sp['ns6'])) 
                st.session_state['ns7'] = bool(int(sp['ns7'])) 
                st.session_state['ns8'] = bool(int(sp['ns8']))
                st.session_state['ns9'] = bool(int(sp['ns9']))  
                st.session_state['ns10'] = bool(int(sp['ns10']))
                st.session_state['ns11'] = bool(int(sp['ns11']))
                st.session_state['ns12'] = bool(int(sp['ns12']))

                if file == "link":
                    st.toast("The URL to the student card could not be loaded correctly", icon="❗")

            xp = parser.get_xp_together(sid, teacher_id)
            if xp is not None:
                st.session_state['ti_xp_together'] = xp
            else:
                st.session_state['ti_xp_together'] = ""

        st.markdown("##### Уникален анонимен номер на детето:")
        st.selectbox("b", student_ids, key="sid", label_visibility="collapsed", index=None, on_change=update_student)

        st.markdown("#### От колко години работите с това дете:")
        st.text_input("От колко години работите с това дете:", key="ti_xp_together", label_visibility="collapsed")

        # ====================================================================================================
        #           Situation and Reaction
        # ====================================================================================================

        st.markdown("\n\n")
        st.markdown("\n\n")
        st.markdown("## Ситуация и реакция" )
        st.markdown(" ")
        st.markdown("##### Дата на :rainbow[случката]:")   
        date = st.date_input("Дата на :rainbow[случката]:", format="DD.MM.YYYY", label_visibility="collapsed") # remove default to make it today

        st.markdown(" ")
        st.markdown("#### **Опишете устно или писмено ситуацията, която се е случила:**")
        st.markdown("(за гласов запис натиснете микрофона)")
        a1, a2 = st.columns([7, 1])
        with a2:
            audio_sit = audio_recorder("", key=st.session_state['audi_sit_key'], pause_threshold=30.)
            transcript_sit, audio_sit_path = transcribe(audio_sit, f"situation_audio.mp3", "text_sit")

        with a1:
            st.text_area("ситуацията", key="text_sit", placeholder="write here", height=257, label_visibility="collapsed")
        
        st.markdown("  ")
        st.markdown("#### **Опишете устно или писмено Вашата реакция:**")
        st.markdown("(за гласов запис натиснете микрофона)")
        b1, b2 = st.columns([7, 1])
        with b2:
            audio_act = audio_recorder("", key=st.session_state['audi_act_key'], pause_threshold=30.)
            transcript_act, audio_act_path = transcribe(audio_act, f"action_audio.mp3", "text_act")
        with b1:
            st.text_area("реакцията", key="text_act", height=257, label_visibility="collapsed")

        st.markdown("#### Опишете устно или писмено **ефекта** от Вашата реакция:")
        st.markdown("(за гласов запис натиснете микрофона)")
        c1, c2 = st.columns([7, 1])
        with c2:
            audio_eff = audio_recorder("", key=st.session_state['audi_eff_key'], pause_threshold=30.)
            transcript_eff, audio_eff_path = transcribe(audio_eff, f"effect_audio.mp3", "text_eff")
        with c1:
            st.text_area("Опишете ефекта от вашата реакция:", key="text_eff", height=257, label_visibility="collapsed")

        # print(st.session_state['text_eff']) TODO

        st.markdown("#### Оценете ефекта от Вашата реакция:")
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

        st.markdown("## Профил на детето")

        if st.session_state['sid'] is not None:

            st.markdown("#### На колко години е ученикът?")
            st.text_input("age", key='ti_age', label_visibility="collapsed")

            st.markdown("#### Пол")
            #print(st.session_state['ra_gender'])
            def gender_to_index(g):
                if g == "мъж":
                    return 0
                elif g == "жена":
                    return 1
                else:
                    return None
            gender = st.radio("g", ("мъж", "жена"), horizontal=True, key='ra_gender', label_visibility="collapsed")

            st.markdown("#### Състояние на детето")

            f1, f2, f3 = st.columns(3)

            with f1:
                st.checkbox("Аутизъм (МКБ:ььь)", key="autism")
                st.checkbox("нз2", key="ns2")
                st.checkbox("нз5", key="ns5")
                st.checkbox("нз8", key="ns8")
                st.checkbox("нз11", key="ns11")

            with f2:
                st.checkbox("Дислексия (МКБ:ььь)", key="dyslexia")
                st.checkbox("нз3", key="ns3")
                st.checkbox("нз6", key="ns6")
                st.checkbox("нз9", key="ns9")
                st.checkbox("нз12", key="ns12")

            with f3:
                st.checkbox("нз1", key="ns1")
                st.checkbox("нз4", key="ns4")
                st.checkbox("нз7", key="ns7")
                st.checkbox("нз10", key="ns10")

            

            if st.session_state['link_profile'] == "":

                
                st.markdown("#### За този ученик няма подадена карта функтионална - Подадете я тук (Опционално)")
                karta = st.file_uploader("Functional Card (Optional)", ALLOWED_DOCUMENT_TYPES, label_visibility="collapsed")
            else:
                st.markdown("#### Картата функционална оценка на детето:")
                
                #st.text_input("профилът", key="link_profile", label_visibility="collapsed")
                t1, t2 = st.columns(2)
                with t1: 
                    st.markdown("###### Линк към картата в нашта система")
                    st.link_button(st.session_state['profile_filename'], st.session_state['link_profile'], use_container_width=True)
                with t2:
                    st.markdown("###### При нова карта тук (Опционално)")
                    karta = st.file_uploader("При нова карта тук (Опционално)", label_visibility="collapsed")      

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
                    if st.session_state['text_eff'] == "":
                        return False
                    if st.session_state['ti_age'] == "":
                        return False
                    if grade == None:
                        return False
                    if gender == None:
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

                    old_student_pr, _ = get_student_data(st.session_state['sid'])
                    new_student_pr = old_student_pr.copy()

                    # print(old_student_pr, "\n\n", new_student_pr)

                    profile_tags = ["autism", "dyslexia", "ns1", "ns2", "ns3", "ns4", "ns5", "ns6", "ns7", "ns8", "ns9", "ns10", "ns11", "ns12"]

                    for tag in profile_tags:
                        new_student_pr[tag] = str(int(st.session_state[tag]))

                    new_student_pr['age'] = st.session_state['ti_age']
                    new_student_pr['gender'] = gender
                    new_student_pr['link functional card'] = st.session_state['link_profile']

                    update = not (new_student_pr == old_student_pr)

                    if update:
                        st.toast("Updating the database of student with new row")
                        parser.add_student_to_db(new_student_pr, teacher_id, st.session_state['sid'])

                    inputs_exel = {
                        "teacher_id": teacher_id,
                        "student_id": st.session_state['sid'],
                        "date": date.strftime("%d-%m-%Y"),
                        "teacher_xp": teacher_xp,
                        "student_age": st.session_state['ti_age'],
                        "xp_with_child": st.session_state['ti_xp_together'],
                        "student_profile": st.session_state['link_profile'],
                        "situation": st.session_state['text_sit'],
                        "action": st.session_state['text_act'],
                        "effect": st.session_state['text_eff'],
                        "grade": grade
                    }


                    new_pr = [label for label in profile_tags if bool(int(new_student_pr[label]))]                    

                    student_pr = {
                        "age": st.session_state['ti_age'],
                        "gender": gender,
                        "profile": new_pr
                    }

                    inputs_form = {
                        "student_profile": student_pr,
                        "situation": st.session_state['text_sit'],
                        "action": st.session_state['text_act'],
                        "effect": st.session_state['text_eff'],
                        "grade": grade
                    }

                    exel = parser.create_exel(inputs_exel)
                    st.session_state['exel'] = exel

                    id_drive = parser.add_form_to_db(inputs_form, teacher_id, audio_sit_path, audio_act_path, audio_eff_path, 
                                            transcript_sit, transcript_act, transcript_eff, st.session_state['sid'], st.session_state['ti_xp_together'])

                    if id_drive and exel:
                        st.session_state['balloons'] = True
                        st.session_state['download'] = True
                    st.rerun()
                else:
                    st.toast("Има още празни полета", icon="❗")
        else:
            st.warning("Моля изберете ученик")
            
        
elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
