import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
import pycountry
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# def load_data(uploaded_file):
#     if uploaded_file.name.endswith('.csv'):
#         return pd.read_csv(uploaded_file)
#     elif uploaded_file.name.endswith(('.xls', '.xlsx')):
#         return pd.read_excel(uploaded_file)
#     else:
#         st.error("Format de fichier non pris en charge. Utilisez CSV ou Excel.")
#         return None

# Analyse de la fraîcheur
def check_freshness(df, date_column, threshold_years=2):
    today = datetime.today()
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df['Obsolete'] = (today - df[date_column]).dt.days > (threshold_years * 365)
    obsolete_count = df['Obsolete'].sum()
    return df[['Obsolete', date_column]].value_counts(), obsolete_count

# Analyse des données manquantes
def check_missing_data(df, required_columns):
    missing_report = {}
    for col in required_columns:
        missing_count = df[col].isnull().sum()
        missing_percentage = (missing_count / len(df)) * 100
        missing_report[col] = {"missing_count": missing_count, "missing_percentage": missing_percentage}
    return pd.DataFrame(missing_report).T

# Validation des codes postaux
def validate_postal_code(df, postal_code_column, valid_length=5):
    df['Invalid_Code'] = df[postal_code_column].apply(
        lambda x: len(str(x)) != valid_length if pd.notnull(x) else True
    )
    invalid_count = df['Invalid_Code'].sum()
    return df[df['Invalid_Code']], invalid_count

# Validation des numéros de téléphone
def validate_phone_number(df, phone_column):
    phone_pattern = r'^\+?[1-9]\d{1,14}$'  # Format E.164
    df['Invalid_Phone'] = df[phone_column].apply(
        lambda x: not re.match(phone_pattern, str(x)) if pd.notnull(x) else True
    )
    invalid_count = df['Invalid_Phone'].sum()
    return df[df['Invalid_Phone']], invalid_count



def validate_nom_prenom(df, nom_column):
    """
    Valide les noms dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        nom_column (str): Le nom de la colonne contenant les noms à valider.

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des noms invalides.
        int: Le nombre total de noms invalides.
    """
    nom_pattern = r'^[A-Za-z\s]+$'  # Noms ne contenant que des lettres et des espaces
    
    df['Invalid_Nom'] = df[nom_column].apply(
        lambda x: not re.match(nom_pattern, str(x)) if pd.notnull(x) else True
    )

    invalid_count = df['Invalid_Nom'].sum()

    return df[df['Invalid_Nom']], invalid_count

def validate_continent(df, continent_column):
    """
    Valide les continents dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        continent_column (str): Le nom de la colonne contenant les continents à valider.

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des continents invalides.
        int: Le nombre total de continents invalides.
    """
    # Liste des continents valides (insensible à la casse)
    valid_continents = ["Africa", "Asia", "Europe", "North America", 
                        "South America", "Oceania", "Antarctica", "Afrique",
                        "Asie", "Europe", "Amérique du nord", "Amérique du sud", "Australie"]
    
    # Validation des continents avec prise en compte de la casse
    df['Invalid_Continent'] = df[continent_column].apply(
        lambda x: x.strip().capitalize() not in valid_continents if pd.notnull(x) else True
    )

    # Compte des continents invalides
    invalid_count = df['Invalid_Continent'].sum()

    return df[df['Invalid_Continent']], invalid_count

def validate_pays(df, pays_column):
    """
    Valide les pays dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        pays_column (str): Le nom de la colonne contenant les pays à valider.

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des pays invalides.
        int: Le nombre total de pays invalides.
    """

    # Liste complète des pays (norme ISO)
    valid_pays = [country.name for country in pycountry.countries]
    
    # Validation
    df['Invalid_Pays'] = df[pays_column].apply(
        lambda x: x.strip().title() not in valid_pays if pd.notnull(x) else True
    )
    
    invalid_count = df['Invalid_Pays'].sum()
    return df[df['Invalid_Pays']], invalid_count

def validate_ville(df, ville_column):
    """
    Valide les villes dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        ville_column (str): Le nom de la colonne contenant les villes à valider.

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des villes invalides.
        int: Le nombre total de villes invalides.
    """
    # Exemple de liste de villes valides (peut être étendue ou remplacée par une API ou une base de données)
    geolocator = Nominatim(user_agent="city_validator")
    
    def is_valid_ville(ville):
        try:
            # Géocoder la ville (timeout pour éviter les blocages)
            location = geolocator.geocode(ville, timeout=10)
            return location is not None
        except GeocoderTimedOut:
            return False

    # Appliquer la validation sur chaque ville
    df['Invalid_Ville'] = df[ville_column].apply(
        lambda x: not is_valid_ville(x) if pd.notnull(x) else True
    )

    # Compte des villes invalides
    invalid_count = df['Invalid_Ville'].sum()

    return df[df['Invalid_Ville']], invalid_count




def validate_email(df, email_column):
    """
    Valide les adresses email dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        email_column (str): Le nom de la colonne contenant les emails à valider.

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des emails invalides.
        int: Le nombre total d'emails invalides.
    """
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    df['Invalid_Email'] = df[email_column].apply(
        lambda x: not re.match(email_pattern, str(x)) if pd.notnull(x) else True
    )

    invalid_count = df['Invalid_Email'].sum()

    return df[df['Invalid_Email']], invalid_count

def validate_date_naissance(df, date_column, date_format='%Y-%m-%d'):
    """
    Valide les dates de naissance dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        date_column (str): Le nom de la colonne contenant les dates de naissance à valider.
        date_format (str): Le format attendu des dates (par défaut '%Y-%m-%d').

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des dates invalides.
        int: Le nombre total de dates invalides.
    """
    def is_valid_date(date):
        try:
            # Vérifier que la date est valide et raisonnable (avant aujourd'hui)
            parsed_date = datetime.strptime(date, date_format)
            return parsed_date <= datetime.now()
        except (ValueError, TypeError):
            return False

    df['Invalid_Date_Naissance'] = df[date_column].apply(
        lambda x: not is_valid_date(x) if pd.notnull(x) else True
    )

    invalid_count = df['Invalid_Date_Naissance'].sum()

    return df[df['Invalid_Date_Naissance']], invalid_count

def validate_date_entree_relation(df, date_column, date_format='%Y-%m-%d'):
    """
    Valide les dates d'entrée en relation dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        date_column (str): Le nom de la colonne contenant les dates à valider.
        date_format (str): Le format attendu des dates (par défaut '%Y-%m-%d').

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des dates invalides.
        int: Le nombre total de dates invalides.
    """
    def is_valid_date(date):
        try:
            # Vérifier que la date est valide
            datetime.strptime(date, date_format)
            return True
        except (ValueError, TypeError):
            return False

    df['Invalid_Date_Entree_Relation'] = df[date_column].apply(
        lambda x: not is_valid_date(x) if pd.notnull(x) else True
    )

    invalid_count = df['Invalid_Date_Entree_Relation'].sum()

    return df[df['Invalid_Date_Entree_Relation']], invalid_count


def validate_adresse_postale(df, adresse_column):
    """
    Valide les adresses postales dans une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        adresse_column (str): Le nom de la colonne contenant les adresses à valider.

    Returns:
        pd.DataFrame: Un sous-DataFrame contenant les lignes avec des adresses invalides.
        int: Le nombre total d'adresses invalides.
    """
    adresse_pattern = r'^[0-9]+\s+[A-Za-z\s,.-]+$'  # Format de base : numéro + rue
    adresse_pattern = r'\d+,\s+[A-Za-z]+\s+[A-Za-z]+'

    df['Invalid_Adresse'] = df[adresse_column].apply(
        lambda x: not re.match(adresse_pattern, str(x)) if pd.notnull(x) else True
    )

    invalid_count = df['Invalid_Adresse'].sum()

    return df[df['Invalid_Adresse']], invalid_count