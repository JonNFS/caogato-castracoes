# Cão & Gato — Sistema de Castrações Comunitárias

Sistema desktop desenvolvido para a Clínica Cão & Gato (Maceió, AL) como parte de um projeto de extensão universitária do curso de Análise e Desenvolvimento de Sistemas.

O objetivo foi substituir o controle manual feito em caderno e calculadora pelo programa de castração comunitária da clínica, que atende tutores de baixa renda com preços reduzidos.

---

## Funcionalidades

- Login com acesso único para a recepção
- Cadastro de castrações com cálculo automático do valor conforme o peso do animal
- Filtro de registros por dia, mês, ano ou todos
- Relatório financeiro com totais de castrações e receita por período
- Gráfico comparativo entre o mês atual e o mês anterior
- Opção de copiar a lista de castrações formatada
- Registro da forma de pagamento: Pix, Cartão ou Espécie
- Banco de dados local, sem necessidade de internet ou mensalidade

---

## Regra de precificação

- Gato: R$ 100,00 fixo, independente do sexo ou peso
- Cao ate 10 kg: R$ 200,00
- Cao acima de 10 kg: R$ 200,00 + R$ 10,00 por kg inteiro excedente

---

## Tecnologias utilizadas

- Python 3.11
- CustomTkinter (interface grafica)
- SQLite (banco de dados local)
- PyInstaller (geracao do executavel)

---

## Como executar

Com Python instalado, instale as dependencias:

```
pip install customtkinter Pillow
```

Depois execute:

```
python main.py
```

O banco de dados e criado automaticamente na primeira execucao.

Para gerar o executavel (.exe), rode o arquivo `build_exe.bat`.

---

## Credenciais de acesso

Login: admin  
Senha: admin

---

Desenvolvido por Jonathan Nunes — 2026
