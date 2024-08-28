import streamlit as st




def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link("app.py", label="Həkimlərə sual ver", icon=":material/contact_support:")
    st.sidebar.page_link("user/mesajlar.py", label="Mesajlar", icon=":material/mail:")
    st.sidebar.page_link("user/umumi.py", label="Ümumi məlumatlarınız", icon=":material/info:")
    st.sidebar.page_link("user/mexfi.py", label="Şifrəni dəyişdir", icon=":material/password:")

    # st.sidebar.page_link("user/cache_example.py", label="Cache example")
    # if st.session_state.role in ["admin", "super-admin"]:
    #     st.sidebar.page_link("pages/admin.py", label="Manage users")
    #     st.sidebar.page_link(
    #         "pages/super-admin.py",
    #         label="Manage admin access",
    #         disabled=st.session_state.role != "super-admin",
    #     )


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("app.py", label="Log in")


def menu():
    # Determine if a user is logged in or not, then show the correct navigation menu
    
    # if "role" not in st.session_state or st.session_state.role is None:
    #     unauthenticated_menu()
    #     return
    st.logo("logo/logo.png", link=None, icon_image=None)
    authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page("app.py")
    menu()