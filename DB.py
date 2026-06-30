
import sqlite3

def criar_banco():
    conn = sqlite3.connect('agrotech.db')
    cursor = conn.cursor()

    # 1. TABELA DE USUÁRIOS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )''')

    # 2. TABELA DE TALHÕES (Ligada ao Usuário)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Talhao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        largura_metros REAL,
        altura_metros REAL,
        area_hectares REAL,
        tipo_solo TEXT,
        FOREIGN KEY (usuario_id) REFERENCES Usuario(id)
    )''')

    # 3. TABELA DE SAFRAS (Ligada ao Talhão)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Safra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        talhao_id INTEGER NOT NULL,
        cultura TEXT NOT NULL,
        data_plantio DATE,
        ciclo_dias INTEGER,
        status TEXT,
        FOREIGN KEY (talhao_id) REFERENCES Talhao(id)
    )''')
    
    # Dentro da sua função criar_banco(), certifique-se de executar:
cursor.execute('''
CREATE TABLE IF NOT EXISTS Insumo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    tipo_semente TEXT NOT NULL,
    quantidade_kg REAL NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id)
)
''')


    conn.commit()
    conn.close()
    print("Sucesso: Banco 'agrotech.db' criado com as tabelas Usuario, Talhao e Safra.")

if __name__ == "__main__":
    criar_banco()
