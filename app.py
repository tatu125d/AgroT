from datetime import datetime, timedelta
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'agrotech_linux_root'

@app.route('/')
def index():
	return redirect(url_for('login'))

def get_db():
    conn = sqlite3.connect('agrotech.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        user = db.execute('SELECT * FROM Usuario WHERE email = ?', (email,)).fetchone()
        
        # O fechamento do banco deve vir DEPOIS de validar tudo
        if user and check_password_hash(user['senha'], senha):
            session['user_id'] = user['id']
            session['nome'] = user['nome']
            db.close() # Feche aqui antes do redirecionamento
            return redirect(url_for('dashboard'))
            
        db.close() # Feche aqui caso as credenciais estejam erradas
        return "Erro nas credenciais"
    return render_template('login.html')
   
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    user_id = session['user_id']

    # --- PROCESSA O CLIQUE DO BOTÃO "LIMPAR TALHÃO" ---
    if request.method == 'POST' and 'liberar_safra_id' in request.form:
        safra_id = request.form.get('liberar_safra_id')
        db.execute("UPDATE Safra SET status = 'Finalizado' WHERE id = ?", (safra_id,))
        db.commit()
        db.close()
        return redirect(url_for('dashboard'))

    # 1. Busca a Área Total Cadastrada nos Talhões
    res_area = db.execute("SELECT SUM(area_hectares) FROM Talhao WHERE usuario_id = ?", (user_id,)).fetchone()
    area_total = float(res_area[0]) if res_area[0] else 0.0

    # 2. Busca o Gráfico (Soma da área por cultura ativa - Ignora as finalizadas)
    dados_grafico = db.execute("""
        SELECT s.cultura, SUM(t.area_hectares) 
        FROM Safra s 
        JOIN Talhao t ON s.talhao_id = t.id 
        WHERE t.usuario_id = ? AND s.status != 'Finalizado'
        GROUP BY s.cultura
    """, (user_id,)).fetchall()

    # Descobre quais culturas o usuário possui de verdade (ex: ['MILHO', 'SOJA'])
    culturas_ativas = [str(item['cultura']).strip().lower() for item in dados_grafico]

    # 3. Calcula a Barra de Uso do Solo (Cultivado vs Não Cultivado)
    res_cultivado = db.execute("""
        SELECT SUM(t.area_hectares) 
        FROM Safra s 
        JOIN Talhao t ON s.talhao_id = t.id 
        WHERE t.usuario_id = ? AND s.status != 'Finalizado'
    """, (user_id,)).fetchone()
    area_cultivada = float(res_cultivado[0]) if res_cultivado[0] else 0.0
    area_disponivel = max(0.0, area_total - area_cultivada)

    # 4. Busca os Plantios Mais Próximos da Colheita (Garantindo o ID e ignorando finalizados)
    safras_raw = db.execute("""
        SELECT s.id as safra_id, t.nome as talhao_nome, s.cultura, s.data_plantio, s.ciclo_dias, s.status
        FROM Safra s 
        JOIN Talhao t ON s.talhao_id = t.id 
        WHERE t.usuario_id = ? AND s.status != 'Finalizado'
    """, (user_id,)).fetchall()

    proximas_colheitas = []
    hoje = datetime.now().date()

    for s in safras_raw:
        if s['data_plantio'] and s['ciclo_dias']:
            try:
                data_p = datetime.strptime(s['data_plantio'], '%Y-%m-%d').date()
                dias_passados = (hoje - data_p).days
                ciclo_total = int(s['ciclo_dias'])
                dias_restantes = ciclo_total - dias_passados
                
                # Se já estiver pronto (dias zerados ou se o status for explicitamente alterado por fora)
                if dias_restantes <= 0 or s['status'] == 'Pronto para Colheita':
                    proximas_colheitas.append({
                        'id': s['safra_id'],
                        'talhao': s['talhao_nome'],
                        'cultura': s['cultura'],
                        'restantes': 0,
                        'pronto': True
                    })
                else:
                    proximas_colheitas.append({
                        'id': s['safra_id'],
                        'talhao': s['talhao_nome'],
                        'cultura': s['cultura'],
                        'restantes': dias_restantes,
                        'pronto': False
                    })
            except:
                pass

    proximas_colheitas = sorted(proximas_colheitas, key=lambda x: x['restantes'])[:3]

    # 5. API de Cotação Dinâmica
    commodities = []
    mapeamento_api = {
        'milho': {'nome': 'Milho', 'codigo': 'CORNUSD', 'padrao': 4.35},
        'soja': {'nome': 'Soja', 'codigo': 'SOYBUSD', 'padrao': 11.85},
        'trigo': {'nome': 'Trigo', 'codigo': 'WHEATUSD', 'padrao': 5.60}
    }

    culturas_para_buscar = [info for nome_cultura, info in mapeamento_api.items() if nome_cultura in culturas_ativas]

    if culturas_para_buscar:
        try:
            import urllib.request
            import json
            codigos_url = "," + ",".join([f"{item['codigo'][:4]}-USD" for item in culturas_para_buscar])
            url_api = f"https://economia.awesomeapi.com.br/last/{codigos_url.strip(',')}"
            
            req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                dados_api = json.loads(response.read().decode())
                
                for item in culturas_para_buscar:
                    chave_api = item['codigo'].replace('-', '')
                    if chave_api in dados_api:
                        commodities.append({
                            'nome': item['nome'],
                            'preco': float(dados_api[chave_api]['bid'])
                        })
        except:
            for item in culturas_para_buscar:
                commodities.append({
                    'nome': item['nome'],
                    'preco': item['padrao']
                })

    db.close()

    return render_template('dashboard.html', 
                           nome=session.get('nome'), 
                           area=area_total,
                           area_cultivada=area_cultivada,
                           area_disponivel=area_disponivel,
                           proximas_colheitas=proximas_colheitas,
                           commodities=commodities,
                           dados_pizza=dados_grafico)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha']) # Segurança!
        
        db = get_db()
        # Insere o novo usuário no banco de dados agrotech.db
        db.execute("INSERT INTO Usuario (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
        db.commit()
        db.close()
        
        # Após cadastrar, manda o usuário para o Login
        return redirect(url_for('login'))
        
    return render_template('cadastro.html')
                  
@app.route('/talhao', methods=['GET', 'POST'])
def talhao():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db = get_db()

    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao in ['salvar', 'editar']:
            nome = request.form.get('nome')
            largura = float(request.form.get('largura') or 0)
            comprimento = float(request.form.get('comprimento') or 0)
            tipo_solo = request.form.get('tipo_solo')
            area_ha = (largura * comprimento) / 10000

            if acao == 'salvar':
                db.execute("INSERT INTO Talhao (usuario_id, nome, largura_metros, altura_metros, area_hectares, tipo_solo) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, nome, largura, comprimento, area_ha, tipo_solo))
            
            elif acao == 'editar':
                id_talhao = request.form.get('id')
                db.execute("UPDATE Talhao SET nome=?, largura_metros=?, altura_metros=?, area_hectares=?, tipo_solo=? WHERE id=? AND usuario_id=?",
                           (nome, largura, comprimento, area_ha, tipo_solo, id_talhao, user_id))
        
        elif acao == 'deletar':
            id_talhao = request.form.get('id')
            db.execute("DELETE FROM Talhao WHERE id=? AND usuario_id=?", (id_talhao, user_id))
        
        db.commit()
        return redirect(url_for('talhao'))

    # --- PARTE DA BUSCA (GET) ---
    busca = request.args.get('busca')
    if busca:
        # Correção da tupla: (user_id, f'%{busca}%')
        talhoes = db.execute("SELECT * FROM Talhao WHERE usuario_id = ? AND nome LIKE ?", (user_id, f'%{busca}%')).fetchall()
    else:
        # Correção da tupla: (user_id,)
        talhoes = db.execute("SELECT * FROM Talhao WHERE usuario_id = ? ORDER BY id DESC LIMIT 5", (user_id,)).fetchall()

    # O return deve estar alinhado com o primeiro 'if' da função
    return render_template('talhao.html', talhoes=talhoes)

@app.route('/safra', methods=['GET', 'POST'])
def safra():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'POST':
        talhao_id = request.form.get('talhao_id')
        insumo_id = request.form.get('insumo_id')
        data_plantio = request.form.get('data_plantio')
        ciclo_dias = request.form.get('ciclo_dias')
        
        # 1. Busca os dados do Talhão e da Semente selecionada
        talhao_info = db.execute("SELECT nome, area_hectares FROM Talhao WHERE id = ?", (talhao_id,)).fetchone()
        semente_info = db.execute("SELECT nome_insumo, quantidade FROM Insumo WHERE id = ?", (insumo_id,)).fetchone()
        
        if not talhao_info or not semente_info:
            db.close()
            return "Erro: Dados inválidos selecionados para o plantio."
            
        area = float(talhao_info['area_hectares'])
        cultura = semente_info['nome_insumo']
        
        # 2. Define a taxa estimada de kg por hectare baseado na cultura
        cultura_lower = cultura.lower()
        if 'soja' in cultura_lower:
            taxa_kg_por_ha = 60.0
        elif 'milho' in cultura_lower:
            taxa_kg_por_ha = 20.0
        else:
            taxa_kg_por_ha = 90.0
            
        total_semente_necessaria = area * taxa_kg_por_ha
        
        # 3. Valida se há saldo suficiente no estoque de Insumos
        if semente_info['quantidade'] < total_semente_necessaria:
            db.close()
            return f"Erro: Estoque insuficiente! Para plantar {cultura} em {talhao_info['nome']} ({area} ha), você precisa de {total_semente_necessaria:.1f} kg de sementes, mas só possui {semente_info['quantidade']:.1f} kg em estoque."
            
        # 4. Deduz a quantidade gasta do estoque de insumos
        nova_quantidade_estoque = semente_info['quantidade'] - total_semente_necessaria
        db.execute("UPDATE Insumo SET quantidade = ? WHERE id = ?", (nova_quantidade_estoque, insumo_id))
        
        # 5. Insere a nova Safra com status ativo 'CRESCENDO'
        db.execute("INSERT INTO Safra (talhao_id, cultura, data_plantio, ciclo_dias, status) VALUES (?, ?, ?, ?, 'CRESCENDO')",
                   (talhao_id, cultura, data_plantio, ciclo_dias))
        db.commit()
        db.close()
        return redirect(url_for('safra'))

    # --- MÉTODO GET ---
    busca_talhao = request.args.get('busca_talhao', '').strip()

    # QUERY MATADORA: Pega talhões que NÃO possuem nenhuma safra em andamento/ativa
    query_base = """
        SELECT id, nome, area_hectares FROM Talhao 
        WHERE usuario_id = ? 
        AND id NOT IN (
            SELECT talhao_id FROM Safra 
            WHERE status != 'Finalizado' AND talhao_id IS NOT NULL
        )
    """
    
    if busca_talhao:
        talhoes = db.execute(query_base + " AND nome LIKE ?", (user_id, f'%{busca_talhao}%')).fetchall()
    else:
        talhoes = db.execute(query_base, (user_id,)).fetchall()

    # Pega sementes tolerando variações de emojis salvas no banco
    sementes_disponiveis = db.execute("""
        SELECT id, nome_insumo, quantidade FROM Insumo 
        WHERE usuario_id = ? 
        AND (categoria LIKE '%Semente%' OR categoria = 'Semente')
        AND quantidade > 0
    """, (user_id,)).fetchall()

    # Busca as safras em andamento para o acompanhamento
    safras_raw = db.execute("""
        SELECT s.id, t.nome as talhao_nome, s.cultura, s.data_plantio, s.ciclo_dias, s.status
        FROM Safra s 
        JOIN Talhao t ON s.talhao_id = t.id 
        WHERE t.usuario_id = ? AND s.status != 'Finalizado'
    """, (user_id,)).fetchall()
    
    safras_processadas = []
    hoje = datetime.now().date()
    
    for s in safras_raw:
        if not s['data_plantio'] or s['ciclo_dias'] is None:
            novo_status = "DADOS INCOMPLETOS"
            data_exibicao = s['data_plantio'] if s['data_plantio'] else "---"
            ciclo_exibicao = 0
        else:
            try:
                data_p = datetime.strptime(s['data_plantio'], '%Y-%m-%d').date()
                dias_passados = (hoje - data_p).days
                ciclo_total = int(s['ciclo_dias'])
                data_exibicao = s['data_plantio']
                ciclo_exibicao = ciclo_total
                
                if s['status'] == 'Pronto para Colheita' or dias_passados >= ciclo_total:
                    novo_status = "PRONTO PARA COLHEITA"
                elif dias_passados < 0:
                    novo_status = "PLANEJADO"
                else:
                    percentual = min(100, int((dias_passados / ciclo_total) * 100))
                    novo_status = f"CRESCENDO ({dias_passados} dias - {percentual}%)"
            except:
                novo_status = "ERRO DE FORMATAÇÃO"
                data_exibicao = s['data_plantio']
                ciclo_exibicao = s['ciclo_dias']
                
        safras_processadas.append({
            'talhao_nome': s['talhao_nome'],
            'cultura': s['cultura'],
            'data_plantio': data_exibicao,
            'ciclo_dias': ciclo_exibicao,
            'status': novo_status
        })

    db.close()
    return render_template('safra.html', talhoes=talhoes, sementes=sementes_disponiveis, safras=safras_processadas, busca_talhao=busca_talhao)
    
@app.route('/insumo', methods=['GET', 'POST'])
def insumo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'POST':
        categoria = request.form.get('categoria')
        # Captura o nome e força ficar em LETRAS MAIÚSCULAS eliminando espaços extras
        nome_insumo = request.form.get('nome_insumo').strip().upper()
        quantidade = float(request.form.get('quantidade') or 0)
        
        # Define a unidade automaticamente baseado na categoria
        unidade = 'Litros' if categoria == 'Defensivo' else 'kg'
        
        # Verifica se este insumo (com o nome já em MAIÚSCULO) já existe para o usuário
        existente = db.execute("""
            SELECT id, quantidade FROM Insumo 
            WHERE usuario_id = ? AND categoria = ? AND nome_insumo = ?
        """, (user_id, categoria, nome_insumo)).fetchone()
        
        if existente:
            # Se já existir exatamente o mesmo nome, apenas soma a quantidade no estoque
            nova_qtd = existente['quantidade'] + quantidade
            db.execute("UPDATE Insumo SET quantidade = ? WHERE id = ?", (nova_qtd, existente['id']))
        else:
            # Se for um nome inédito, cria o registro do zero
            db.execute("""
                INSERT INTO Insumo (usuario_id, categoria, nome_insumo, quantidade, unidade) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, categoria, nome_insumo, quantidade, unidade))
            
        db.commit()
        db.close()
        return redirect(url_for('insumo'))
        
    # Busca o estoque do banco para listar na tela
    estoque = db.execute("""
        SELECT id, categoria, nome_insumo, quantidade, unidade 
        FROM Insumo WHERE usuario_id = ? 
        ORDER BY categoria, nome_insumo
    """, (user_id,)).fetchall()
    
    db.close()
    return render_template('insumo.html', estoque=estoque, nome=session.get('nome'))

@app.route('/historico')
def historico():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    user_id = session['user_id']
    
    # Busca safras ativas para montar o calendário futuro
    safras_ativas = db.execute("""
        SELECT s.id, t.nome as talhao_nome, s.cultura, s.data_plantio, s.ciclo_dias
        FROM Safra s
        JOIN Talhao t ON s.talhao_id = t.id
        WHERE t.usuario_id = ? AND s.status != 'Finalizado'
    """, (user_id,)).fetchall()
    
    eventos_calendario = []
    
    for s in safras_ativas:
        if s['data_plantio'] and s['ciclo_dias']:
            try:
                # Trata a data de plantio
                data_plantio_str = s['data_plantio'].split()[0]
                data_p = datetime.strptime(data_plantio_str, '%Y-%m-%d').date()
                ciclo_total = int(s['ciclo_dias'])
                
                # Projeta os manejos
                data_defensivo = data_p + timedelta(days=20)
                data_fertilizante = data_p + timedelta(days=40)
                data_colheita = data_p + timedelta(days=ciclo_total)
                
                # Formata as informações para o FullCalendar (padrão ISO YYYY-MM-DD)
                # Usamos cores diferentes para cada tipo de manejo para ficar fácil de ler
                eventos_calendario.append({
                    'title': f"🛡️ Defensivo: {s['cultura']} ({s['talhao_nome']})",
                    'start': data_defensivo.strftime('%Y-%m-%d'),
                    'backgroundColor': '#ef4444', # Vermelho
                    'borderColor': '#ef4444'
                })
                
                eventos_calendario.append({
                    'title': f"🌱 Fertilizante: {s['cultura']} ({s['talhao_nome']})",
                    'start': data_fertilizante.strftime('%Y-%m-%d'),
                    'backgroundColor': '#3b82f6', # Azul
                    'borderColor': '#3b82f6'
                })
                
                eventos_calendario.append({
                    'title': f"🚜 COLHEITA: {s['cultura']} ({s['talhao_nome']})",
                    'start': data_colheita.strftime('%Y-%m-%d'),
                    'backgroundColor': '#10b981', # Verde
                    'borderColor': '#10b981'
                })
                
            except Exception as e:
                print(f"Erro no talhão {s['talhao_nome']}: {e}")
                
    db.close()
    
    # Importamos o json para passar a lista de forma correta para o JavaScript
    import json
    eventos_json = json.dumps(eventos_calendario)
    
    return render_template('historico.html', eventos_json=eventos_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
app.run(host='0.0.0.0', port=5000, debug=True)
