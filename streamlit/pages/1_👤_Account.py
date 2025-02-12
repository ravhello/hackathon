import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Account",
    page_icon="👤",
    layout="wide"
)

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
    st.title("👤 Compte Utilisateur")
    
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManager()
    
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Mot de passe", type="password")
            login_submitted = st.form_submit_button("Se connecter")
            
            if login_submitted:
                user = st.session_state.user_manager.verify_user(login_email, login_password)
                if user is not None:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user
                    st.success("Connexion réussie!")
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect")
    
    with tab2:
        with st.form("signup_form"):
            signup_email = st.text_input("Email")
            signup_password = st.text_input("Mot de passe", type="password")
            age = st.number_input("Âge", min_value=18, max_value=100)
            gender = st.selectbox("Genre", ["M", "F"])
            country = st.selectbox("Pays", ["FRA", "GBR", "USA"])
            signup_submitted = st.form_submit_button("S'inscrire")
            
            if signup_submitted:
                if st.session_state.user_manager.add_user(
                    signup_email, signup_password, age, gender, country
                ):
                    st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")
                else:
                    st.error("Cet email est déjà utilisé")
    
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.write("---")
        if st.button("Se déconnecter"):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.rerun()

if __name__ == "__main__":
    main()
