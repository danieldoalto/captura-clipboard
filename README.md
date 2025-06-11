# Captura Clipboard

Um aplicativo Windows para captura automática de imagens do clipboard desenvolvido em Python com CustomTkinter.

## Características

- Interface moderna e responsiva com tema escuro/claro
- Monitoramento automático do clipboard para detecção de imagens (PrintScreen)
- Visualização em tempo real das imagens capturadas
- Seleção múltipla de imagens para salvar
- Salvamento de imagens individuais com numeração sequencial
- Opção para criar arquivo ZIP com todas as imagens selecionadas
- Configuração centralizada via arquivo YAML

## Requisitos

- Python 3.7+
- Windows (testado no Windows 10/11)
- Bibliotecas Python (veja `requirements.txt`):
  - customtkinter
  - pillow
  - pyperclip

## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

Execute o programa principal:

```bash
python main.py
```

## Uso

1. **Iniciando a captura**:
   - Inicie o programa
   - Opcional: Digite um prefixo para os nomes dos arquivos
   - Clique em "Iniciar Captura"
   - Use a tecla PrintScreen ou outra ferramenta para copiar imagens para o clipboard
   - As imagens serão automaticamente capturadas e exibidas

2. **Salvando imagens**:
   - Clique em "Salvar Imagens"
   - Selecione ou desmarque as imagens que deseja salvar
   - Escolha se deseja criar um arquivo ZIP
   - Clique em "Salvar Selecionadas"
   - Escolha o diretório de destino

3. **Finalizando**:
   - Clique em "Finalizar Captura" para parar o monitoramento
   - Clique em "Sair" para fechar o aplicativo

## Configuração

O arquivo `config.yml` contém todas as configurações do aplicativo:

- Configurações de aplicativo (título, tamanho, tema)
- Configurações de imagem (tamanho de visualização, formato)
- Configurações de salvamento (prefixo padrão, diretório)
- Configurações de monitoramento (intervalo)
- Configurações de log (nível de log, arquivo)

## Estrutura do Projeto

- `main.py` - Ponto de entrada do aplicativo
- `app.py` - Interface principal e lógica do aplicativo
- `clipboard_monitor.py` - Módulo para monitoramento do clipboard
- `image_manager.py` - Módulo para gerenciamento de imagens
- `logger.py` - Configuração de logging
- `config.yml` - Arquivo de configuração
- `requirements.txt` - Dependências do projeto

## Notas

- O monitoramento é feito em uma thread separada para não bloquear a interface
- As imagens são mantidas em memória até serem salvas ou o programa ser fechado
- Para melhor desempenho, não deixe o aplicativo capturando por longos períodos com muitas imagens

## Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo LICENSE para obter detalhes.
