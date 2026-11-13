
from pwdlib import PasswordHash

# Configuration du hachage sécurisé
password_hash = PasswordHash.recommended()


# Transformer un mot de passe en hash
def hash_password(password: str):
    return password_hash.hash(password)


# Vérifier un mot de passe
def verify_password(password: str, hashed_password: str):
    return password_hash.verify(password, hashed_password)
