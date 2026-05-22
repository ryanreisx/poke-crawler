# poke-crawler

Crawler para extrair informações detalhadas de Pokémon específicos a partir do portal Bulbapedia.

## Requisitos
- Python 3.11+
- Dependencias em `requirements.txt`

## Executando localmente
```bash
python main.py charmander pikachu pidgey
```

## Executando com Docker
### Build
```bash
docker build -t poke-crawler .
```

### Run
```bash
docker run --rm poke-crawler charmander pikachu pidgey
```

### Persistindo banco/imagens no host
```bash
docker run --rm -v ${PWD}/data:/app/data poke-crawler charmander pikachu pidgey
```

No PowerShell, se `${PWD}` falhar, use caminho absoluto:
```powershell
docker run --rm -v C:\caminho\para\poke-crawler\data:/app/data poke-crawler charmander pikachu pidgey
```
