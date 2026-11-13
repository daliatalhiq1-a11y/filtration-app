
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL

# Configuration de la connexion MySQL
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password="DALIA1234@TALHIQ",
    host="localhost",
    port=3306,
    database="filtration_db",
    query={"charset": "utf8mb4"}
)

# Création du moteur de connexion
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

# Gestion des sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base pour les modèles
Base = declarative_base()


# Fonction de connexion à la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Test de connexion
if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            print("Connexion MySQL réussie !")
            print("Base de données : filtration_db")
    except Exception as e:
        print("Erreur de connexion MySQL :", e)
