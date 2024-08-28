import streamlit as st
# import base64
# import aides
# import asyncio
# from menu import menu
st.set_page_config(page_title="medAId.az", page_icon=None, layout="centered")
# menu()

@st.experimental_fragment
def change_pwd():
    with st.container(border=True):
        curr_pwd=st.text_input("Cari şifrənizi daxil edin:", max_chars=20, type='password',)
        new_pwd=st.text_input("Yeni şifrənizi daxil edin:", max_chars=20, type='password')
        new_pwd_again=st.text_input("Yeni şifrənizi təkrar edin:", max_chars=20, type='password')
        if st.button('Şifrəni dəyişdir'):
            st.write("Şifrəniz yenisilə uğurla dəyişdirildi.")

st.html("<h6>Şifrənizi dəyişdirə bilərsiniz</h6>")
change_pwd()
