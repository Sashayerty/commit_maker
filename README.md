# Commit Maker [![Created with Python](https://img.shields.io/badge/Created_with-Python-blue)](https://www.python.org/) [![Created with uv](https://img.shields.io/badge/Created_with-uv-blue)]()

## Все коммиты в репозитории - результат работы программы.

Эта CLI-утилита автоматически создает осмысленные сообщения для git-коммитов, используя Mistral AI на основе вывода команд `git status` и `git diff`.

## Возможности

- Автоматически генерирует содержательные сообщения коммитов на русском языке
- Интерактивное подтверждение перед созданием коммита
- Работает как с существующими Git-репозиториями, так и с новыми
- Использует API Mistral AI для интеллектуального формирования сообщений

## Требования

- Установленный Git в системе
- API-ключ Mistral

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

1. Перейдите в папку с вашим Git-репозиторием
2. Запустите скрипт:
   ```bash
   python commit_maker.py
   ```
3. Следуйте интерактивным подсказкам:
   - Для существующих репозиториев: проверьте и подтвердите сгенерированное ИИ сообщение коммита
   - Для новых репозиториев: выберите, нужно ли инициализировать Git-репозиторий и сделать начальный коммит

## Создание исполняемого файла с помощью pyinstaller

### Linux/MacOS
1. Устанавливаем pyinstaller:
   ```bash
   # pip
   pip3 install pyinstaller
   # uv
   uv add pyinstaller
   ```
2. Выполняем:
   ```bash
   # pip
   pyinstaller --onefile commit_maker.py
   # uv 
   uv run pyinstaller --onefile commit_maker.py
   ```
3. Создается 2 директории: `./dist` и `./build`, нам нужна `./dist`, там лежит `commit_maker`
4. Перемещение файла и превращение в исполняемый:
   ```bash
   sudo mv ./dist/commit_maker /usr/bin # После этого все готово к работе!
   ```
### Windows:
1. Устанавливаем pyinstaller:
   ```bash
   # pip
   pip install pyinstaller
   # uv
   uv add pyinstaller
   ```
2. Выполняем:
   ```bash
   # pip
   pyinstaller --onefile commit_maker.py
   # uv 
   uv run pyinstaller --onefile commit_maker.py
   ```
3. Создается 2 директории: `./dist` и `./build`, нам нужна `./dist`, там лежит `commit_maker.exe`
4. Создаем папку `commit_maker` в `C:/Program Files/`. Далее копируем файл `commit_maker.exe` из `./dist` и перемещаем в  `C:/Users/User/Program Files/commit_maker`. Далее открываем Панель управления -> Система и безопасность -> Система -> Дополнительные параметры системы -> Переменные среды -> Path(в системных переменных)(двойной клик) -> Создать. Добавляем `C:/Program Files/commit_maker`. После вышеописанных действий, у Вас в консоли должно все заработать. Пример использования:  
```cmd
commit_maker.exe
```

## Примечания

- Скрипт покажет сгенерированное сообщение коммита перед его созданием
- Вы можете повторно сгенерировать сообщение, нажав 'r' при запросе подтверждения
- По умолчанию сообщения генерируются на русском языке (можно изменить в скрипте)

## Лицензия

Commit Maker лицензирован [MIT](LICENSE)