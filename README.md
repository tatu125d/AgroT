# AgroT

Como você não usa Docker nem Java, adaptei o README para refletir exatamente a tecnologia que você está usando (Python/Flask e PostgreSQL).
Aqui está o modelo pronto. É só copiar, colar no seu arquivo README.md e preencher os campos entre colchetes [ ].
# [Agrotech] - https://credible-rework-visiting.ngrok-free.dev/dashboard
Este projeto é um sistema de gestão agrícola integrado, desenvolvido para otimizar o controle de safras, talhões e estoque.
### 1. Visão Geral
 * **Nome do Projeto:** Archotech
 * **Subdomínio de Acesso:** https://credible-rework-visiting.ngrok-free.dev/dashboard
 * **Arquitetura:** Monolito (Aplicação Flask integrada)
### 2. Banco de Dados
 * **Tecnologia:** PostgreSQL
 * **Nome do Banco:** agrot
 * **Instruções de Acesso:** O sistema utiliza credenciais padrão de ambiente. Para testes locais, certifique-se de que o banco está rodando na porta 5432.
### 3. Stack Tecnológica
 * **Backend:** Python 3.x com framework Flask.
 * **Frontend:** HTML5, CSS3 e Jinja2 (templates integrados no Flask).
 * **Porta de Execução:** 5000
### 4. Planejamento de Testes e Acesso
Para testar a aplicação, o banco de dados deve estar populado.
 * **Arquivo SQL:** Disponível em /scripts/init.sql (ou na raiz do projeto).
 * **Credenciais de Teste:**
   * **Usuário:** postgres 
   * **Senha:** ( sem senha )
 * **Como testar:**
   1. Certifique-se de ter as dependências instaladas: pip install -r requirements.txt
   2. Suba o banco de dados Postgres.
   3. Execute o comando: python app.py
   4. Acesse via http://localhost:5000 ou pelo link exposto via Ngrok.
### 5. Contato em caso de erros
Em caso de falhas no ambiente, erros de conexão com banco de dados ou problemas na execução, entre em contato com:
 * **Responsável:** Alexandre Henrique 
 * **E-mail:** alexandr3hddo@gmail.com
