# Commit Maker [![Created with Python](https://img.shields.io/badge/Created_with-Python-blue)](https://www.python.org/) [![Created with uv](https://img.shields.io/badge/Created_with-uv-purple)](https://docs.astral.sh/uv/) [![Created with ollama](https://img.shields.io/badge/Created_with-ollama-white)](https://ollama.com/)

## Все коммиты в репозитории - результат работы программы

Эта CLI-утилита автоматически создает осмысленные сообщения для git-коммитов, используя локальные модели через ollama/Mistral AI API на основе вывода команд `git status` и `git diff`. Реализована в виде одного файла для удобства перевода в исполняемый файл.

1. [Возможности](#возможности)
2. [Требования](#требования)
   - [Mistral](#получение-api-ключа-mistral-ai)
   - [Ollama](#установка-ollama)
3. [Установка](#установка)
4. [Настройка переменных окружения](#настройка-переменных-окружения)
   - [Windows](#windows)
   - [Linux/MacOS](#linuxmacos)
5. [Использование](#использование)
6. [Создание исполняемого файла](#создание-исполняемого-файла-с-помощью-pyinstaller)
7. [Примечания](#примечания)
8. [Лицензия](#лицензия)

## Возможности

- Автоматически генерирует содержательные сообщения коммитов на русском языке
- Интерактивное подтверждение перед созданием коммита
- Работает как с существующими Git-репозиториями, так и с новыми
- Использование локальных моделей/Mistral AI API для формирования сообщений коммитов на основе изменений в репозитории.

## Требования

- Установленный Git в системе
- API-ключ Mistral (для использования Mistral AI API)
- Установленная ollama в системе (для использования локальных моделей)

### Получение API ключа Mistral AI

Для получения ключа необходимо перейти сайт консоли [Mistral](https://console.mistral.ai/api-keys) и создать API ключ. Для получения необходим аккаунт [Mistral](https://auth.mistral.ai/ui/login).

### Установка ollama

Для установки ollama переходим на сайт [Ollama](https://ollama.com/download) и выбираем способ, подходящий для Вашей системы.

## Установка

```bash
git clone https://github.com/Sashayerty/commit_maker
cd ./commit_maker
```

## Настройка переменных окружения

### Windows

1. Откройте Командную строку от имени Администратора
2. Установите API-ключ Mistral:

   ```cmd
   setx MISTRAL_API_KEY "ваш_api_ключ_здесь"
   ```

3. Перезапустите терминал/IDE для применения изменений

### Linux/macOS

1. Откройте терминал
2. Добавьте в файл конфигурации вашей оболочки (`~/.bashrc`, `~/.zshrc` или `~/.bash_profile`):

   ```bash
   export MISTRAL_API_KEY="ваш_api_ключ_здесь"
   ```

3. Перезагрузите конфигурацию:

   ```bash
   source ~/.bashrc  # или другой файл, который вы редактировали
   ```

## Использование

1. Перейдите в папку с склонированным Git-репозиторием
2. Запустите скрипт:

   ```bash
   # Windows
   python commit_maker.py
   # Linux/MacOS
   python3 commit_maker.py
   ```

3. Следуйте интерактивным подсказкам:
   - Для существующих репозиториев: проверьте и подтвердите сгенерированное ИИ сообщение коммита
   - Для новых репозиториев: выберите, нужно ли инициализировать Git-репозиторий и сделать начальный коммит

## Создание исполняемого файла с помощью pyinstaller

### Общая часть для Windows/Linux/MacOS

1. Устанавливаем pyinstaller:

   ```bash
   # pip Linux/MacOS
   pip3 install pyinstaller
   # pip Windows
   pip install pyinstaller
   # uv Windows/Linux/MacOS
   uv add pyinstaller
   ```

2. Выполняем:

   ```bash
   # pip
   pyinstaller --onefile commit_maker.py
   # uv 
   uv run pyinstaller --onefile commit_maker.py
   ```

### Linux/MacOS

3. Создается 2 директории: `./dist` и `./build`, нам нужна `./dist`, там лежит `commit_maker`
4. Перемещаем файл в папку с исполняемыми бинарниками:

   ```bash
   sudo mv ./dist/commit_maker /usr/bin # После этого все готово к работе!
   ```

### Windows

3. Создается 2 директории: `./dist` и `./build`, нам нужна `./dist`, там лежит `commit_maker.exe`
4. Создаем папку `commit_maker` в `C:/Program Files/`. Далее копируем файл `commit_maker.exe` из `./dist` и перемещаем в  `C:/Users/User/Program Files/commit_maker`. Далее открываем Панель управления -> Система и безопасность -> Система -> Дополнительные параметры системы -> Переменные среды -> Path(в системных переменных)(двойной клик) -> Создать. Добавляем `C:/Program Files/commit_maker`. После вышеописанных действий, у Вас в консоли должно все заработать. 

### Использование:

   ```bash
   commit_maker [OPTION] [VALUE]
   ```

### Пример использования:

   ```bash
   commit_maker -l -m 300 -M qwen2.5:14b # Используем локальные модели, ограничение длины сообщения коммита 300 символов, используем qwen2.5:14b
   ```

## Примечания

- Для просмотра всех возможных опций выполнения скрипта добавьте флаг `--help`
- Скрипт покажет сгенерированное сообщение коммита перед его созданием
- Вы можете повторно сгенерировать сообщение, нажав 'r' при запросе подтверждения
- По умолчанию сообщения генерируются на русском языке (можно изменить в скрипте)

## Лицензия

Commit Maker лицензирован [MIT](LICENSE)
