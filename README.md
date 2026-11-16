# GF ECONOMIC AI v3

Calendário primário via API pública ShowMyTrades (sem chave), com janela de até 7 dias, moedas principais, impacto alto/médio, actual/forecast/previous quando publicados. A API informa timestamps UTC e pode atualizar o conteúdo em cache de 15 minutos.

## Rodar localmente
Python 3.10+. Instale: `pip install -r requirements.txt`; copie `.env.example` para `.env`; execute `python app.py`; abra `http://127.0.0.1:5000`.

## Deploy no Render
Suba o projeto a um repositório GitHub e conecte-o como Web Service no Render. Build `pip install -r requirements.txt`; Start `gunicorn app:app`. Configure `DATABASE_PATH=/var/data/gf_economic_ai.db` e disco persistente. Confira custos do serviço e disco.

## Fonte e uso
Calendário: https://showmytrades.com/docs/api/economic-calendar
Atribuição: Economic calendar by ShowMyTrades, https://showmytrades.com/tools/economic-calendar
Verifique termos e cobertura antes de uso comercial. O provedor declara que permite uso comercial com condições, mas não revenda isolada do calendário.

## Estado e limites
- O calendário é consultado quando a página é aberta; não há agendador de fundo ainda.
- O código ainda não chama a OpenAI API, não analisa direção e não conecta feed de preços/velas.
- Eventos com campos vazios permanecem sem inferência. A avaliação é AGUARDAR ou REVISÃO NECESSÁRIA.
- Não há conexão com IQ Option nem execução de ordens.
- Para análise de 2 e 5 minutos, adicionar fonte de cotações/velas e testar latência, qualidade e fuso antes de produzir qualquer sinal.
- A FMP Free não foi usada para calendário porque seu endpoint econômico tem acesso limitado e a documentação indica que alguns endpoints, incluindo calendário de earnings, são premium. Confirme o plano antes de depender dela.
