
import sqlite3
from werkzeug.security import generate_password_hash

def popular():
    conn = sqlite3.connect('agrotech.db')
    cursor = conn.cursor()

    # 1. Criar um Usuário de teste (Senha: 123)
    senha_cripto = generate_password_hash('123')
    cursor.execute('''
        INSERT OR IGNORE INTO Usuario (id, nome, email, senha) 
        VALUES (1, 'Mario Oliveira', 'mario@email.com', ?)
    ''', (senha_cripto,))

    # 2. Criar Talhões para o Usuário 1
    # Dados baseados no seu Figma (Talhão A e B)
    talhoes = [
        (1, 1, 'Talhão A', 3.5, 120, 80, 'Argiloso'),
        (2, 1, 'Talhão B', 3.0, 100, 100, 'Arenoso')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO Talhao (id, usuario_id, nome, area_hectares, largura_metros, altura_metros, tipo_solo) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', talhoes)

    # 3. Criar Safras para esses Talhões
    safras = [
        (1, 'Milho', '2026-03-01', 120, 'CRESCENDO'),
        (2, 'Soja', '2026-02-15', 110, 'PLANTADA')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO Safra (talhao_id, cultura, data_plantio, ciclo_dias, status) 
        VALUES (?, ?, ?, ?, ?)
    ''', safras)

    conn.commit()
    conn.close()
    print("Dados de teste inseridos com sucesso!")

if __name__ == "__main__":
    popular()
