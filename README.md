# QAhub | Gerador de Massa de Teste

Programa em Python com interface gráfica moderna (CustomTkinter) que gera planilhas Excel (`.xlsx`)
com dados fake (nome, CPF, CNPJ, endereço, etc.) para uso em massa de teste
de QA.

## Como funciona

O programa tem duas abas:

### Aba "Gerar planilha"
1. Marque as colunas que a planilha deve ter. Elas ficam na planilha **na ordem em que você as seleciona**.
2. No painel **Ordem na planilha**, use ▲ e ▼ para reorganizar as colunas.
3. Digite a quantidade de registros (linhas) e marque ou desmarque **Incluir título na planilha** (primeira linha com o nome das colunas).
4. Clique em **Gerar planilha** e escolha onde salvar o arquivo.

Ao marcar **Data de nascimento** ou **Idade**, uma caixinha abre perguntando se
você quer limitar por idade (ex: 14 a 64 anos) ou por ano de nascimento (ex:
1990 a 2015). O filtro vale para as duas colunas ao mesmo tempo, já que a
idade é calculada a partir da data de nascimento sorteada. Use o botão ⚙ ao
lado de qualquer uma das duas para reabrir essa configuração.

#### CPF e CNPJ sem pontuação
Ao lado das colunas **CPF** e **CNPJ** há uma caixinha **"sem pontos"**. Marque
para gerar só os números (ex.: `12345678901`), sem os pontos, barra e traço.
Cada documento tem seu próprio interruptor, então dá pra deixar o CPF sem
pontuação e o CNPJ formatado, por exemplo. A mesma opção existe na aba
"Dado único".

#### Regras da senha
Clique no ⚙ ao lado de **Senha** para escolher a quantidade de caracteres e
quais tipos entram: letras maiúsculas, minúsculas, números e caracteres
especiais. É preciso marcar pelo menos um tipo. As mesmas regras valem tanto
para a planilha quanto para a aba "Dado único".

#### Filtro de estados
Clique no ⚙ ao lado de **Estado (UF)** para escolher quais estados podem
aparecer na coluna (por exemplo, só os estados do Sul). Deixe todos marcados
para não restringir.

#### Filtro de cidade
Clique no ⚙ ao lado de **Cidade** e digite as cidades que podem aparecer, uma por
linha (ex.: `Uberlândia`, `Patos de Minas`). Deixe em branco para sortear qualquer
cidade. O programa não liga a cidade ao estado: se você filtrar as duas colunas,
combine os filtros de forma coerente.

#### Faixa de CEP
Clique no ⚙ ao lado de **CEP** e informe o CEP inicial e o final (8 dígitos, com ou
sem traço). Os CEPs são sorteados dentro dessa faixa numérica, o que é útil para
simular uma região (o primeiro dígito do CEP indica a região do país). Eles têm o
formato correto, mas **não são garantidamente CEPs que existem de verdade**.

#### Nome só masculino ou feminino
Clique no ⚙ ao lado de **Nome completo** ou **Sexo** e escolha "Somente feminino",
"Somente masculino" ou "Ambos". O nome e o sexo continuam coerentes entre si.

#### Domínio de e-mail
Clique no ⚙ ao lado de **E-mail** e informe um domínio (ex.: `empresa.com.br`). Todos
os e-mails saem com `@empresa.com.br`. Em branco, o domínio é aleatório.

#### Duplicatas propositais
No painel **Configuração**, marque **Incluir duplicatas propositais** e informe quantas
linhas devem ser cópias exatas de outras linhas da planilha. O total de linhas
continua sendo o que você pediu: as duplicatas substituem linhas já geradas.
Útil para testar a detecção de duplicidade do sistema.

#### Colunas personalizadas
Clique em **＋ Nova coluna personalizada** para criar uma coluna própria: dê um nome
(ex.: `Perfil de acesso`) e liste os valores possíveis, um por linha
(`Admin`, `Usuário`, `Visitante`). Em cada linha da planilha o programa sorteia
um desses valores. Dicas:

- Repita um valor para ele sair com mais frequência (ex.: `Ativo` 3 vezes e `Inativo` 1 vez).
- Marque **Usar os valores em sequência** para percorrer a lista em ordem (1ª linha = 1º valor, 2ª linha = 2º valor...) e voltar ao início ao chegar no fim.
- Use o botão ✎ ao lado da coluna para editar ou excluir.
- As colunas personalizadas ficam salvas no arquivo `colunas_personalizadas.json`
  (na mesma pasta do programa) e aparecem de novo na próxima vez que você abrir.

### Aba "Gerar dado único"
Gera um único valor fake na tela (igual a geradores avulsos como o 4devs):
CPF, CNPJ, cartão de crédito (com escolha de bandeira: Visa, Mastercard,
American Express, Discover, Diners Club, JCB, Maestro), RG, telefone,
celular, CEP, e-mail ou senha. No CEP e no e-mail valem a mesma faixa e o mesmo domínio configurados na planilha. No cartão de crédito saem também a **validade** e o **CVV** (4 dígitos na American Express, 3 nas demais). No CPF e no CNPJ
há a opção "Sem pontuação". Na senha, o botão **Alterar regras** abre as
mesmas opções de caracteres da aba de planilha. Tem um botão **Copiar** para
colar o valor direto onde precisar.

## Colunas disponíveis (aba "Gerar planilha")

- Nome completo
- CPF
- CNPJ
- Nome da empresa
- Data de nascimento
- Idade
- Sexo
- Estado civil
- E-mail
- Telefone
- Celular
- RG
- Endereço
- Bairro
- Cidade
- Estado (UF)
- CEP
- Senha
- Cartão de crédito
- Bandeira do cartão
- Validade do cartão
- CVV do cartão

Todos os dados são fictícios, gerados com a biblioteca [Faker](https://faker.readthedocs.io/)
no formato brasileiro (`pt_BR`), incluindo CPF e CNPJ com dígitos
verificadores válidos (mas **não pertencem a pessoas reais**).

## Como rodar

```bash
pip install -r requirements.txt
python gerador_massa_teste.py
```

> Importante: o arquivo `logo-qahub.png` precisa estar na mesma pasta do
> `gerador_massa_teste.py`, pois é ele que aparece no topo da janela.

## Tecnologias

- Python 3
- CustomTkinter (interface moderna, baseada no Tkinter que já vem com o Python)
- Pillow (para exibir a logo com qualidade)
- Faker (geração de dados fake em pt_BR)
- Pandas + openpyxl (geração da planilha Excel)

## Aviso

Os dados gerados são apenas para fins de teste de software. Não use para
nenhuma outra finalidade.
