import streamlit as st
# import base64
# import aides
# import asyncio
# from menu import menu
st.set_page_config(page_title="medAId.az", page_icon=None, layout="wide")

# menu()

st.html("<h6>Ümumi məlumat</h6>")
st.markdown("Topladığımız məlumatlar xəstələyiniz haqqında daha doğru qərar verməyə komək edəcəkdir.<br>Yaşayış və doğum yeri məlumatlarınız ətrafınızda ola biləcək xəstəliklər haqqında Sizi məlumatlandırmağa kömək edəcəkdir.", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1.container(border=True):
        age = st.number_input("Yaşınız", min_value=18, max_value=100, step=1)
        weight = st.number_input("Çəkiniz (kg)", min_value=50, max_value=300, step=1)
        gender=st.selectbox("Cinsiyyətiniz",["Qadın","Kişi"],placeholder="Cinsiyyətinizi seçin")
with col2.container(border=True):
        birth_region = st.selectbox("Doğum yeri", ["Baku", "Sumqayıt", "Gəncə"])
        residence_region = st.selectbox("Yaşayış yeri", ["Baku", "Sumqayıt", "Gəncə"])

col3, col4 = st.columns(2)
with col3.container(border=True):
        smoking = st.selectbox("Siqaret/e-siqaret çəkirsiz?", ["Xeyr","Bəli"])
        if smoking == "Bəli":
            smoking_frequency = st.selectbox("Hansı sıxlıqla?", ["Gündə maks. 5 ədəd", "Gündə maks. 10 ədəd", "Gündə maks. 1 paket", "Gündə 1 paketdən çox"])
with col4.container(border=True):
        alcohol = st.selectbox("Spirtli içki içirsiz?", ["Xeyr","Bəli"])
        if alcohol == "Bəli":
            alcohol_frequency = st.selectbox("Hansı sıxlıqla?", ["Gündə maks. 50 ml", "Gündə maks. 100 ml", "Gündə maks. 0.5 litr", "Gündə 0.5 litrdən çox"])
col5, col6=st.columns(2)

with col5.container(border=True):
    medical_history = st.text_input("Hər hansı xronik xəstəliyiniz var?", max_chars=100,placeholder=" Varsa ad(lar)ını yazın")
with col6.container(border=True):
    allergies = st.multiselect("Bilinən hər hansı ciddi allergiyanız var?", ["Yoxdur","Dərman", "Qida", "Heyvan", "Ətraf mühit/mövsum", "Başqa"],["Yoxdur"],placeholder='Müvafiq olanı seçin.')
    if "Başqa" in allergies:
        other_allergies = st.text_input("Nə cür allergiyanız var?", max_chars=100)