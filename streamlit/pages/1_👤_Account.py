import streamlit as st
import pandas as pd
from utils import load_data, find_country, COUNTRY_FLAGS

st.set_page_config(
    page_title="Account",
    page_icon="👤",
    layout="wide"
)

df = load_data()

class UserManager:
    def __init__(self):
        self.users = pd.DataFrame(columns=[
            'UserID', 'Email', 'Password', 'Age', 'Gender', 'Country', 
            'ClientID', 'ClientSegment'  # Added ClientSegment
        ])
    
    def add_user(self, email, password, age, gender, country):
        if email in self.users['Email'].values:
            return False
        
        user_id = len(self.users) + 1
        # Generate a unique ClientID
        client_id = len(self.users) + 1000000
        
        # Assign a default segment based on some logic
        # For example, new users start as "NEW"
        client_segment = "INACTIVE_1Y"
        
        new_user = pd.DataFrame({
            'UserID': [user_id],
            'Email': [email],
            'Password': [password],
            'Age': [age],
            'Gender': [gender],
            'Country': [country],
            'ClientID': [client_id],
            'ClientSegment': [client_segment]
        })
        self.users = pd.concat([self.users, new_user], ignore_index=True)
        return True
    
    def verify_user(self, email, password):
        user = self.users[self.users['Email'] == email]
        if len(user) == 0:
            return None
        user = user.iloc[0]
        if user['Password'] == password:
            return user.to_dict()
        return None

def main():
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    # Check if user is logged in
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        # Display personalized header with user info
        user_data = st.session_state.user_data
        country_flag = COUNTRY_FLAGS[user_data['Country']]
        st.title(f"👤 {user_data['Email']}'s Account {country_flag}")
        
        # Display user information
        st.write("### Your Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Email:** {user_data['Email']}")
            st.write(f"**Age:** {user_data['Age']}")
        with col2:
            st.write(f"**Gender:** {user_data['Gender']}")
            st.write(f"**Country:** {user_data['Country']} {country_flag}")
        
        # Logout button
        st.write("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            find_country(mode="reset")
            st.rerun()
    
    else:
        # Show regular login page
        st.title("👤 User Account")
        
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
                        st.switch_page("1_🏠_Home.py")
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

if __name__ == "__main__":
    main()
