import streamlit as st
import pandas as pd
from utils import load_data, find_country

st.set_page_config(
    page_title="Account",
    page_icon="👤",
    layout="wide"
)

df = load_data()

class UserManager:
    def __init__(self):
        self.users = pd.DataFrame(columns=['UserID', 'Email', 'Password', 'Age', 'Gender', 'Country'])
    
    def add_user(self, email, password, age, gender, country):
        if email in self.users['Email'].values:
            return False
        
        user_id = len(self.users) + 1
        new_user = pd.DataFrame({
            'UserID': [user_id],
            'Email': [email],
            'Password': [password],
            'Age': [age],
            'Gender': [gender],
            'Country': [country]
        })
        self.users = pd.concat([self.users, new_user], ignore_index=True)
        return True

    def verify_user(self, email, password):
        user = self.users[
            (self.users['Email'] == email) & 
            (self.users['Password'] == password)
        ]
        return None if user.empty else user.iloc[0]

def main():
    st.title("👤 User Account")
    
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                user = st.session_state.user_manager.verify_user(login_email, login_password)
                if user is not None:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user
                    st.session_state.country = user['Country']
                    st.success("Login successful!")
                    # Redirect to home page
                    st.switch_page("1_🏠_Home.py")  # Make sure the filename matches your home page
                else:
                    st.error("Incorrect email or password")
    
    with tab2:
        with st.form("signup_form"):
            signup_email = st.text_input("Email")
            signup_password = st.text_input("Password", type="password")
            age = st.number_input("Age", min_value=18, max_value=100)
            gender = st.selectbox("Gender", ["M", "F"])
            country = st.selectbox("Country", df['StoreCountry'].unique())
            signup_submitted = st.form_submit_button("Sign Up")
            
            if signup_submitted:
                if st.session_state.user_manager.add_user(
                    signup_email, signup_password, age, gender, country
                ):
                    st.success("Registration successful! You can now login.")
                else:
                    st.error("This email is already in use")
    
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.write("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            find_country(mode="reset")
            st.rerun()

if __name__ == "__main__":
    main()






# import streamlit as st
# import pandas as pd
# from utils import load_data, find_country

# st.set_page_config(
#     page_title="Account",
#     page_icon="👤",
#     layout="wide"
# )

# df = load_data()

# class UserManager:
#     def __init__(self):
#         self.users = pd.DataFrame(columns=['UserID', 'Email', 'Password', 'Age', 'Gender', 'Country'])
    
#     def add_user(self, email, password, age, gender, country):
#         if email in self.users['Email'].values:
#             return False
        
#         user_id = len(self.users) + 1
#         new_user = pd.DataFrame({
#             'UserID': [user_id],
#             'Email': [email],
#             'Password': [password],
#             'Age': [age],
#             'Gender': [gender],
#             'Country': [country]
#         })
#         self.users = pd.concat([self.users, new_user], ignore_index=True)
#         return True

#     def verify_user(self, email, password):
#         user = self.users[
#             (self.users['Email'] == email) & 
#             (self.users['Password'] == password)
#         ]
#         return None if user.empty else user.iloc[0]

# def main():
#     st.title("👤 User Account")
    
#     if 'user_manager' not in st.session_state:
#         st.session_state.user_manager = UserManager()
    
#     tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
#     with tab1:
#         with st.form("login_form"):
#             login_email = st.text_input("Email")
#             login_password = st.text_input("Password", type="password")
#             login_submitted = st.form_submit_button("Login")
            
#             if login_submitted:
#                 user = st.session_state.user_manager.verify_user(login_email, login_password)
#                 print(user['Country'])
#                 if user is not None:
#                     st.session_state.logged_in = True
#                     st.session_state.user_data = user
#                     st.session_state.country = user['Country']
#                     st.success("Login successful!")
#                     st.rerun()
#                 else:
#                     st.error("Incorrect email or password")
    
#     with tab2:
#         with st.form("signup_form"):
#             signup_email = st.text_input("Email")
#             signup_password = st.text_input("Password", type="password")
#             age = st.number_input("Age", min_value=18, max_value=100)
#             gender = st.selectbox("Gender", ["M", "F"])
#             country = st.selectbox("Country", df['StoreCountry'].unique())
#             signup_submitted = st.form_submit_button("Sign Up")
            

#             if signup_submitted:
#                 if st.session_state.user_manager.add_user(
#                     signup_email, signup_password, age, gender, country
#                 ):
#                     st.success("Registration successful! You can now login.")
#                 else:
#                     st.error("This email is already in use")
    
#     if 'logged_in' in st.session_state and st.session_state.logged_in:
#         st.write("---")
#         if st.button("Logout"):
#             st.session_state.logged_in = False
#             st.session_state.user_data = None
#             find_country(mode="reset")
#             st.rerun()

# if __name__ == "__main__":
#     main()
