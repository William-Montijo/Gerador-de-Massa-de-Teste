![QAhub](assets/logo-qahub.png)

# QAhub — gerador de massa de teste

Gera dados falsos em **português do Brasil** para testar sistemas: planilha
Excel, CSV ou JSON com as colunas que você escolher, e um dado único avulso
com botão de copiar.

Este é o **QAhub em Python/Streamlit** — a mesma ideia do site feito em React,
agora pronto para subir no Streamlit Community Cloud a partir de um repositório
no GitHub.

## O que ele faz

**Aba "Gerar planilha"**
- 41 colunas prontas + colunas personalizadas que você criar
- Modelos próprios: selecione as colunas, clique em "Criar modelo", dê um nome e ele fica no topo para usar com um clique. Cada pessoa vê só os seus
- Botão **Limpar seleção** deixa a planilha com zero colunas (o app abre assim)
- Prévia das 8 primeiras linhas antes de baixar
- Download em **Excel (.xlsx)**, **CSV** ou **JSON**
- Histórico das 8 últimas gerações, para baixar de novo sem configurar outra vez

**Aba "Gerar dado único"**
- CPF, CNPJ, cartão com validade e CVV, RG, telefone, celular, CEP, e-mail, senha,
  PIX, CNH, PIS/NIT, título de eleitor, placa, código de barras, UUID, valor,
  conta bancária e data de cadastro
- Cada valor sai pronto para copiar

**Aba "Gerar arquivo"**
- Escolha a extensão (pdf, png, zip, exe… ou qualquer outra) e o tamanho em bytes, KB ou MB, e baixe um arquivo com **exatamente** esse tamanho, até 100 MB
- Atalhos de 1 KB, 100 KB, 1 MB, 5 MB, 10 MB e 50 MB
- Conteúdo vazio (bytes zero), aleatório (não compacta) ou texto legível
- Opção de começar com o cabeçalho real do formato (PDF, PNG, JPG, ZIP, DOCX…) para passar em validações que olham o tipo real. O arquivo não abre no programa do formato

**Aba "E-mail temporário"**
- Cria um endereço descartável (nome sorteado ou escolhido por você, domínio à escolha) e mostra as mensagens que chegarem nele, sem encher a sua caixa pessoal
- Vários endereços ao mesmo tempo, cada um com uma anotação (ex.: "cadastro da loja") para você não se perder durante o dia
- Ao abrir uma mensagem, destaca os **possíveis códigos de verificação** e os **links** (confirmar e-mail, redefinir senha), cada um com botão de copiar
- Atualização manual ou automática a cada 10 segundos, apagar mensagem, apagar endereço e baixar o HTML do e-mail
- Usa a API gratuita do [Mail.tm](https://mail.tm) (limite de 8 consultas por segundo por IP). Se aparecer o erro 429 (muitas consultas), rode `python -m qahub.diagnostico_email` para ver o que o serviço respondeu. Os endereços ficam só na sessão: se recarregar a página, saem da lista. Use só em sites que você tem permissão de testar; alguns sites bloqueiam endereços temporários

## Dados coerentes

- **CEP, cidade, estado e DDD sempre da mesma região** — se a pessoa é de
  Uberlândia/MG, o CEP cai na faixa de MG e o telefone tem DDD de MG
- **CPF, CNPJ, CNH, PIS/NIT, título de eleitor e código de barras** com dígito
  verificador calculado de verdade
- **Cartão de crédito** passa na regra de Luhn, com prefixo da bandeira
- **PIX** usa o dado da própria linha: escolheu CPF, a chave é o CPF daquela
  pessoa; escolheu celular, é o celular dela
- **Sujeira na planilha**, quando você quer testar o que quebra o sistema:
  linhas duplicadas, mesmo CPF em nomes diferentes, e-mail com caixa diferente
  ou espaços, campo vazio e linha em branco
- Filtros por estado, cidade, faixa de CEP, sexo, domínio de e-mail, idade ou
  ano de nascimento, escolaridade, faixa de renda, valor fixo ou faixa de valor
- **RG, telefone e celular** podem sair com a pontuação de costume
  (`12.345.678-X`, `(11) 91234-5678`) ou só com números (`12345678X`,
  `11912345678`) — basta marcar a caixinha ao lado do nome da coluna
- O filtro de **estado e DDD** vale para a planilha e também para a aba
  "Gerar dado único": escolha os estados e o telefone, o celular, o CEP e a
  chave PIX saem só daquela região

## Como rodar no computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

## Como publicar no Streamlit Cloud

1. Suba esta pasta para um repositório no GitHub.
2. Entre em <https://share.streamlit.io> com a sua conta do GitHub.
3. Escolha o repositório, o arquivo **`app.py`** e a branch **`main`**.
4. Clique em **Deploy**. O `requirements.txt` instala o resto sozinho.

## Estrutura

```text
app.py                      interface Streamlit (as abas)
qahub/brasil.py             estados, faixas de CEP, DDDs, cidades e dígitos verificadores
qahub/geradores.py          cada coluna, o dado único e as conferências de dígito
qahub/config.py             estado inicial e colunas personalizadas
qahub/planilha.py           exportação em Excel, CSV e JSON
qahub/arquivos.py           arquivos de teste com extensão e tamanho exatos
qahub/emailtemp.py          e-mail temporário (API do Mail.tm)
qahub/diagnostico_email.py  script que mostra o que o Mail.tm responde (erro 429 etc.)
qahub/historico.py          as últimas gerações da sessão
tests/test_regras.py        49 testes das regras
tests/test_arquivos.py      testes do gerador de arquivos
tests/test_emailtemp.py     testes do e-mail temporário (sem internet, com respostas simuladas)
tests/test_diagnostico_email.py  testes do script de diagnóstico
assets/logo-qahub.png       logo
```

## Testes

```bash
pip install pytest
python -m pytest tests/ -q
```

Os testes cobrem: coerência de CEP/cidade/estado/DDD, dígitos verificadores de
CPF, CNPJ, CNH, PIS, título e boleto, regra de Luhn nos cartões, os cinco tipos
de chave PIX, a sujeira na planilha, a conferência de dígitos, os filtros de
escolaridade, renda, valor e estado/DDD, o formato dd/mm/aaaa, a pontuação de
RG, telefone e celular, os modelos do usuário e o nome dos arquivos.

## Tecnologias

Python 3 · Streamlit · Faker (pt_BR) · openpyxl · requests · pytest
