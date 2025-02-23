import pandas as pd
import re
from sqlalchemy import create_engine

class Expectation:
    """Classe contenant des méthodes pour vérifier la qualité des données (DataFrame ou SQL)."""

    @staticmethod
    def ExpectColumnValuesToNotBeNull(df, column):
        """Vérifie qu'aucune valeur n'est nulle dans une colonne spécifique."""
        total_count = df[column].shape[0]
        unexpected_values = df[df[column].isnull()][column].tolist()
        unexpected_count = len(unexpected_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToNotBeNull({column})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": unexpected_values,
            "success": unexpected_count == 0  # True si aucune erreur, False sinon
        }

    @staticmethod
    def ExpectColumnValuesToBeBetween(df, column, min_value, max_value):
        """Vérifie que toutes les valeurs d'une colonne sont comprises entre min_value et max_value."""
        total_count = df[column].notnull().sum()  # Ignorer les valeurs nulles
        unexpected_values = df[(df[column] < min_value) | (df[column] > max_value)][column].tolist()
        unexpected_count = len(unexpected_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToBeBetween({column}, {min_value}, {max_value})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": unexpected_values,
            "success": unexpected_count == 0
        }

    @staticmethod
    def ExpectColumnValuesToMatchRegex(df, column, regex):
        """Vérifie que toutes les valeurs d'une colonne respectent une expression régulière."""
        total_count = df[column].notnull().sum()  # Ignorer les valeurs nulles
        unexpected_values = df[~df[column].astype(str).str.match(regex, na=False)][column].tolist()
        unexpected_count = len(unexpected_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToMatchRegex({column}, '{regex}')",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": unexpected_values,
            "success": unexpected_count == 0
        }
        
    @staticmethod
    def ExpectColumnValuesToBeUnique(df, column):
        """Vérifie que toutes les valeurs d'une colonne sont uniques en ignorant les valeurs manquantes."""
        non_null_series = df[column].dropna()  # Exclut les NaN
        total_count = non_null_series.shape[0]
        duplicated_values = non_null_series[non_null_series.duplicated()].tolist()
        unexpected_count = len(duplicated_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToBeUnique({column})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": duplicated_values,
            "success": unexpected_count == 0
        }

        
    @staticmethod
    def ExpectColumnValuesToBeWithinIQR(df, column, factor=1.5):
        """Vérifie que les valeurs sont dans une plage normale basée sur l'IQR."""
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR

        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)][column].tolist()
        unexpected_count = len(outliers)
        unexpected_percent = round((unexpected_count / df[column].notnull().sum()) * 100, 2) if df[column].notnull().sum() > 0 else 0

        return {
            "check": f"ExpectColumnValuesToBeWithinIQR({column})",
            "element_count": df[column].notnull().sum(),
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": outliers,
            "success": unexpected_count == 0
        }
        
    @staticmethod
    def ExpectColumnValuesToBeInSet(df, column, valid_values):
        """Vérifie que toutes les valeurs d'une colonne appartiennent à une liste prédéfinie."""
        total_count = df[column].notnull().sum()
        invalid_values = df[~df[column].isin(valid_values)][column].tolist()
        unexpected_count = len(invalid_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToBeInSet({column})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": invalid_values,
            "success": unexpected_count == 0
        }
    
    @staticmethod
    def ExpectColumnValuesToHaveLengthBetween(df, column, min_length, max_length):
        """Vérifie que les chaînes de caractères ont une longueur entre min_length et max_length."""
        total_count = df[column].notnull().sum()
        invalid_values = df[(df[column].astype(str).str.len() < min_length) | 
                            (df[column].astype(str).str.len() > max_length)][column].tolist()
        unexpected_count = len(invalid_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToHaveLengthBetween({column}, {min_length}, {max_length})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": invalid_values,
            "success": unexpected_count == 0
        }

    @staticmethod
    def ExpectColumnValuesToRespectOrder(df, column1, column2):
        """Vérifie que les valeurs de column1 sont toujours inférieures ou égales à celles de column2."""
        total_count = df[column1].notnull().sum()
        invalid_values = df[df[column1] > df[column2]][[column1, column2]].values.tolist()
        unexpected_count = len(invalid_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToRespectOrder({column1}, {column2})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": invalid_values,
            "success": unexpected_count == 0
        }
        
    @staticmethod
    def ExpectColumnValuesToBeInDateRange(df, column, min_date, max_date):
        """Vérifie que toutes les dates sont dans la plage spécifiée."""
        df[column] = pd.to_datetime(df[column], errors='coerce')  # Convertir en date
        total_count = df[column].notnull().sum()
        invalid_values = df[(df[column] < min_date) | (df[column] > max_date)][column].tolist()
        unexpected_count = len(invalid_values)
        unexpected_percent = round((unexpected_count / total_count) * 100, 2) if total_count > 0 else 0

        return {
            "check": f"ExpectColumnValuesToBeInDateRange({column}, {min_date}, {max_date})",
            "element_count": total_count,
            "unexpected_count": unexpected_count,
            "unexpected_percent": unexpected_percent,
            "unexpected_list": invalid_values,
            "success": unexpected_count == 0
        }
        
    @staticmethod
    def ExpectRowCompletenessToBeAboveThreshold(df, threshold=0.8):
        """Vérifie que les enregistrements(lignes) contiennent au moins un certain pourcentage de valeurs non nulles."""
        row_completeness = df.notnull().mean(axis=1)  # Pourcentage de colonnes remplies par ligne
        invalid_rows = df[row_completeness < threshold].index.tolist()
        unexpected_count = len(invalid_rows)

        return {
            "check": f"ExpectRowCompletenessToBeAboveThreshold({threshold * 100}%)",
            "element_count": df.shape[0],
            "unexpected_count": unexpected_count,
            "unexpected_percent": round((unexpected_count / df.shape[0]) * 100, 2) if df.shape[0] > 0 else 0,
            "unexpected_list": invalid_rows,
            "success": unexpected_count == 0
        }






class DataFrameContext:
    """Gestionnaire de contexte pour appliquer des vérifications sur un DataFrame ou une base SQL."""

    def __init__(self, data_source, sql_query=None, db_engine=None):
        """
        data_source : soit un DataFrame Pandas, soit une chaîne de connexion SQL
        sql_query : si on utilise une base de données, la requête SQL à exécuter
        db_engine : connexion SQLAlchemy pour accéder à la base de données
        """
        if isinstance(data_source, pd.DataFrame):
            self.df = data_source
        elif isinstance(data_source, str) and sql_query and db_engine:
            # Charger les données depuis la base SQL
            self.df = pd.read_sql(sql_query, db_engine)
        else:
            raise ValueError("Le paramètre data_source doit être un DataFrame Pandas ou une connexion SQL avec une requête.")

        self.reports = []

    def __enter__(self):
        print("📂 Entrée dans le contexte des données")
        return self  # Permet d'accéder à self dans le bloc `with`

    def apply_expectation(self, expectation_func, *args, **kwargs):
        """
        Applique une fonction de vérification de la classe Expectation.
        expectation_func : méthode statique de Expectation
        args/kwargs : paramètres supplémentaires pour la fonction de vérification
        """
        try:
            report = expectation_func(self.df, *args, **kwargs)
            self.reports.append(report)
        except Exception as e:
            print(f"🚨 Erreur lors de l'exécution de {expectation_func.__name__} : {e}")

    def __exit__(self, exc_type, exc_value, traceback):
        print("📂 Sortie du contexte des données")
        print("📊 Rapport de validation :")
        for report in self.reports:
            print(report)
