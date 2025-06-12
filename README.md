# Captura Clipboard

Um aplicativo Windows para captura automática de imagens do clipboard desenvolvido em Python com CustomTkinter.

## Características

- Interface moderna e responsiva com tema escuro/claro.
- Monitoramento automático da área de transferência para detecção de imagens.
- Estrutura modularizada para melhor manutenção e escalabilidade (classes em arquivos dedicados).
- Diálogo de gerenciamento de imagens aprimorado:
  - Visualização de miniaturas das imagens capturadas.
  - Reordenação de imagens com funcionalidade de arrastar e soltar (drag-and-drop).
  - Pré-visualização de imagens individuais com duplo clique.
  - Seleção múltipla de imagens para salvar.
- Opções de salvamento flexíveis:
  - Salvamento de imagens individuais com numeração sequencial e prefixo personalizável.
  - Criação de arquivo ZIP contendo as imagens selecionadas.
- Configuração centralizada via arquivo `config.yml`.
- Logging detalhado para facilitar o rastreamento e depuração.

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

1. **Interface Principal**:
   - A linha superior contém um campo para definir o **Prefixo** dos arquivos, e os botões **"Iniciar Captura"**, **"Pausar Captura"**, e **"Visualizar Imagens"**.
   - A barra de status inferior exibe o estado do monitoramento, a contagem de imagens, e os botões **"Ajuda"** e **"Sair"**.

2. **Capturando Imagens**:
   - Opcionalmente, defina um **Prefixo** para os nomes dos arquivos.
   - Clique em **"Iniciar Captura"**. O aplicativo começará a monitorar a área de transferência.
   - Copie imagens para a área de transferência (ex: usando a tecla PrintScreen ou Ctrl+C em uma imagem).
   - As imagens capturadas são adicionadas automaticamente.
   - Para interromper temporariamente, clique em **"Pausar Captura"**.

3. **Gerenciando e Salvando Imagens**:
   - Clique em **"Visualizar Imagens"** para abrir o diálogo de gerenciamento.
   - **Visualizar**: Miniaturas de todas as imagens capturadas são exibidas.
   - **Pré-visualizar**: Dê um duplo clique em qualquer miniatura para ver a imagem em tamanho maior.
   - **Reordenar**: Clique e arraste uma miniatura para uma nova posição para alterar a ordem de salvamento.
   - **Selecionar**: Marque ou desmarque as caixas de seleção abaixo de cada miniatura para incluir ou excluir imagens do salvamento.
   - Após organizar e selecionar, clique em **"Aplicar Alterações"** para confirmar as mudanças na ordem e seleção, ou **"Cancelar"** para descartá-las.
   - De volta à janela principal, defina o **Prefixo** desejado (se ainda não o fez).
   - Escolha se deseja **"Criar arquivo ZIP"**.
   - Clique em **"Salvar Imagens Selecionadas"** (este botão pode estar na janela principal ou o salvamento ser iniciado a partir do diálogo de visualização, dependendo da implementação final da UI após "Aplicar Alterações").
   - Selecione a pasta de destino.

4. **Ajuda e Saída**:
   - Clique em **"Ajuda"** para ver informações detalhadas sobre o uso do aplicativo.
   - Clique em **"Sair"** para fechar o aplicativo. As imagens não salvas serão descartadas após confirmação.

## Configuração

O arquivo `config.yml` contém todas as configurações do aplicativo:

- Configurações de aplicativo (título, tamanho, tema)
- Configurações de imagem (tamanho de visualização, formato)
- Configurações de salvamento (prefixo padrão, diretório)
- Configurações de monitoramento (intervalo)
- Configurações de log (nível de log, arquivo)

## Estrutura do Projeto

O projeto foi modularizado para melhorar a organização e manutenibilidade:

- `main.py`: Ponto de entrada da aplicação. Inicializa e executa a interface principal.
- `app.py`: Define a classe `ClipboardApp`, que constitui a janela principal da interface gráfica e coordena as interações do usuário e a lógica central da aplicação.
- `clipboard_monitor.py`: Contém a classe `ClipboardMonitor`, responsável por monitorar a área de transferência em uma thread separada para detectar novas imagens.
- `image_manager.py`: Inclui a classe `ImageManager`, que gerencia o armazenamento, metadados, criação de miniaturas e operações de salvamento das imagens capturadas.
- `image_selection_dialog.py`: Define a classe `ImageSelectionDialog`, uma janela de diálogo que permite aos usuários visualizar miniaturas, selecionar, reordenar (via drag-and-drop) e pré-visualizar (via duplo clique) as imagens capturadas antes de salvar.
- `image_viewer_dialog.py`: Apresenta a classe `ImageViewerDialog`, um diálogo simples para exibir uma única imagem em um tamanho maior.
- `config_manager.py`: Provê a classe `ConfigManager` (ou similar) para carregar e fornecer acesso às configurações definidas no arquivo `config.yml`.
- `logger_setup.py` (ou `logger.py`): Script ou módulo que configura o sistema de logging para a aplicação, permitindo registrar eventos e erros em um arquivo ou no console.
- `tooltip.py`: (Se aplicável) Classe para criar tooltips customizados para widgets da interface.
- `config.yml`: Arquivo de configuração centralizado em formato YAML, contendo parâmetros para a interface, processamento de imagens, salvamento, logging, etc.
- `requirements.txt`: Lista todas as bibliotecas Python necessárias para executar o projeto.
- `help.md`: Arquivo Markdown com instruções detalhadas de uso para o usuário final.
- `README.md`: Este arquivo, fornecendo uma visão geral do projeto, instruções de instalação e uso.

## Notas

- O monitoramento é feito em uma thread separada para não bloquear a interface
- As imagens são mantidas em memória até serem salvas ou o programa ser fechado
- Para melhor desempenho, não deixe o aplicativo capturando por longos períodos com muitas imagens

## Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo LICENSE para obter detalhes.
