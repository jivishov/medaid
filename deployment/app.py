import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.rerun()

def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()


login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

generalinfo = st.Page("user/umumi.py", title="Ümumi sağlamlıq məlumatınız", icon=":material/info:")
lab_history=st.Page("user/cache_example.py",title="Analiz tarixçəsi", icon=":material/history:")
askquestion = st.Page("user/sualver.py", title="Həkimə sual ver", icon=":material/contact_support:", default=True)
msg_inbox = st.Page("user/chatdoc.py", title="Gələn mesajlar", icon=":material/inbox:" )
msg_outbox = st.Page("user/outbox.py", title="Gedən mesajlar", icon=":material/outbox:" )
passwd = st.Page("user/mexfi.py", title="Şifrənizi dəyişdirin", icon=":material/password:")
public_doc_profile= st.Page("doctors/public_profile.py", title="Həkim Profili", icon=":material/badge:")
edit_doc_profile= st.Page("doctors/save_profile.py", title="Həkim Profili Redaktə", icon=":material/badge:")

    # st.sidebar.page_link("app.py", label="Həkimlərə sual ver", icon=":material/contact_support:")
    # st.sidebar.page_link("user/mesajlar.py", label="Mesajlar", icon=":material/mail:")
    # st.sidebar.page_link("user/umumi.py", label="Ümumi məlumatlarınız", icon=":material/info:")
    # st.sidebar.page_link("user/mexfi.py", label="Şifrəni dəyişdir", icon=":material/password:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Tibbi məlumatlar": [ generalinfo, lab_history],
            "Həkimlərlə əlaqə": [askquestion, msg_inbox, msg_outbox],
            "Məxfi": [passwd],
            "Həkim profili": [public_doc_profile,edit_doc_profile],
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()