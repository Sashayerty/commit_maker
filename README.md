# Генератор сообщений для коммитов с использованием ИИ

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
   python commit_generator.py
   ```
3. Следуйте интерактивным подсказкам:
   - Для существующих репозиториев: проверьте и подтвердите сгенерированное ИИ сообщение коммита
   - Для новых репозиториев: выберите, нужно ли инициализировать Git-репозиторий и сделать начальный коммит

## Примечания

- Скрипт покажет сгенерированное сообщение коммита перед его созданием
- Вы можете повторно сгенерировать сообщение, нажав 'r' при запросе подтверждения
- По умолчанию сообщения генерируются на русском языке (можно изменить в скрипте)

## Лицензия

Commit Maker лицензирован [MIT](LICENSE)