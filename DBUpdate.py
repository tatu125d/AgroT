import sqlite3

def atualizar_banco_insumos_completo():
    conn = sqlite3.connect('agrotech.db')
    cursor = conn.cursor()
    
    print("Atualizando estrutura da tabela Insumo...")
    
    # Remove a tabela antiga para evitar conflitos
    cursor.execute("DROP TABLE IF EXISTS Insumo")
    
    # Cria a nova tabela sem tokens invalidos para o SQLite
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Insumo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        categoria TEXT NOT NULL,
        nome_insumo TEXT NOT NULL,
        quantidade REAL NOT NULL,
        unidade TEXT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES Usuario(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Sucesso total! A tabela 'Insumo' foi criada perfeitamente.")

if __name__ == "__main__":
    atualizar_banco_insumos_completo()
