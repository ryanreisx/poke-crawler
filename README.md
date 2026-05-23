# Poke Crawler

Crawler assíncrono em Python para extração, normalização e persistência de dados de Pokémon a partir da Bulbapedia.

## Objetivo

Dado uma lista de nomes de Pokemons, o projeto:

1. Consulta a pagina do Pokemon na Bulbapedia.
2. Faz parsing defensivo do HTML.
3. Normaliza os dados em modelos Pydantic.
4. Baixa a imagem do Pokemon para uma pasta local.
5. Persiste os dados em SQLite via SQLAlchemy (com upsert).

## Dados extraidos

Para cada Pokemon, o crawler coleta:

- **Dados gerais**: nome, número nacional da Pokédex e categoria.
- **Tipagem**: lista de tipos.
- **Base stats**: HP, Attack, Defense, Sp. Atk, Sp. Def, Speed.
- **Evolução**: antecessor e sucessor (quando houver).
- **Habilidades**: nome da habilidade e indicador de hidden ability.
- **Imagem**: arquivo salvo localmente e caminho associado ao Pokemon.

## Arquitetura

O projeto utiliza arquitetura em camadas para separar responsabilidades e reduzir acoplamento.

| Camada | Responsabilidade |
|---|---|
| clients | Requisições HTTP externas |
| parsers | Parsing e extração de dados HTML |
| models | Contratos e validação de dados com Pydantic |
| services | Orquestração do crawler e concorrência |
| database | Persistência, ORM, repositories e Unit of Work |
| runner | Fluxo de execução do job |
| main.py | Entry point da CLI |

## Estrutura do projeto

```text
app/
├── clients/
│   └── bulbapedia_client.py
├── parsers/
│   └── pokemon_parser.py
├── models/
│   ├── pokemon.py
│   ├── ability.py
│   └── evolutions.py
├── services/
│   ├── pokemon_service.py
│   └── image_service.py
├── database/
│   ├── base.py
│   ├── connection.py
│   ├── unit_of_work.py
│   ├── models/
│   │   └── pokemon_model.py
│   └── repositories/
│       └── pokemon_repository.py
├── exceptions/
│   └── parsing_error.py
├── logging_config.py
└── runner.py
main.py
requirements.txt
README.md
tests/
├── fixtures/
└── parsers/
```

## Requisitos

- Python 3.11+
- Dependências em `requirements.txt`

## Instalação

```bash
pip install -r requirements.txt
```

## Execução local

Passe os Pokemons como argumentos posicionais:

```bash
python main.py charmander pikachu pidgey
```

No PowerShell:

```powershell
python main.py charmander pikachu pidgey
```

## Concorrencia

A execucao em lote usa asyncio com controle de concorrencia via Semaphore. Cada Pokemon é processado em task assincrona, com isolamento de persistência por operação (Unit of Work).

## Persistência

- Banco local SQLite (`data/pokemon.db`).
- ORM com SQLAlchemy.
- Imagens salvas em `data/images`
- Estrategia de upsert para evitar duplicidade e permitir reprocessamento.
- Sincronização estrita para coleções (types e abilities).

## Modelo de dados

O banco foi modelado de forma relacional para evitar duplicidade e facilitar reprocessamentos.

### Principais entidades

| Tabela | Responsabilidade |
|---|---|
| `pokemon` | Dados principais do Pokémon |
| `pokemon_stats` | Status do Pokémon |
| `pokemon_types` | Tipos do Pokémon |
| `pokemon_abilities` | Habilidades do Pokémon |
| `pokemon_evolutions` | Cadeia evolutiva |

## Logs

Logs estruturados foram adicionados para:

- falha por Pokemon;
- classificacao de erro (ex.: `not_found`, `parsing_error`, `network_error`).

## Resiliência e tratamento de falhas

- Requisicoes HTTP com retry/backoff exponencial via Tenacity.
- Retry aplicado apenas para falhas temporarias:
  - timeout/rede;
  - status 429 (rate limit);
  - erros HTTP 5xx.
- Parsing defensivo com validacao de campos obrigatorios e formatos esperados.

## Docker

### Build

```bash
docker build -t poke-crawler .
```

### Run

```bash
docker run --rm poke-crawler charmander pikachu pidgey
```

### Persistindo banco/imagens no host

```powershell
docker run --rm -v "${PWD}\data:/app/data" poke-crawler charmander pikachu pidgey
```

Fallback com caminho absoluto no Windows:

```powershell
docker run --rm -v "C:\seu-caminho\poke-crawler\data:/app/data" poke-crawler charmander pikachu pidgey
```

## Testes

Executar testes:

```bash
pytest
```

## Decisoes técnicas

- **HTTPX**: escolhido por suporte nativo a async/await e boa ergonômia para concorrência.
- **BeautifulSoup**: simplifica parsing HTML e navegação por elementos.
- **Arquitetura em camadas**: separa coleta HTTP, parsing, orquestração e persistência para baixo acoplamento.
- **asyncio**: coordenação de tasks para processar vários Pokemons no mesmo job.
- **Tenacity**: retries com backoff para resiliência a falhas transitorias.
- **Parsing defensivo**: validação de existência/formato dos campos antes de extrair.
- **Pydantic**: normalização e consistência de tipos antes da persistência.
- **SQLite + SQLAlchemy**: simplicidade local com ORM e possibilidade de evolução.