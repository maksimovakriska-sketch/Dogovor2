ContractsApp — краткая инструкция после установки

1) После инсталляции:
   - Приложение будет доступно по адресу http://127.0.0.1:8000 (если установлен сервис через NSSM).
   - Если вы не устанавливали службу, можно запустить exe вручную:
       C:\Program Files\ContractsApp\ContractsApp.exe serve --host 0.0.0.0 --port 8000

2) Данные (SQLite): по умолчанию файл contracts.db лежит в каталоге установки (C:\Program Files\ContractsApp).
   - Если хотите хранить БД в другом месте (ProgramData/AppData), задайте переменную окружения CONTRACTS_DB
     например: CONTRACTS_DB=sqlite:///C:/ProgramData/ContractsApp/contracts.db

3) Управление службой (NSSM):
   - Остановить: nssm stop ContractsAppService
   - Запустить: nssm start ContractsAppService
   - Удалить: nssm remove ContractsAppService confirm

4) Безопасность:
   - Если сервер будет доступен по сети, рекомендуется настроить nginx или reverse proxy и HTTPS.
   - Для работы в локальной сети откройте порт в брандмауэре (например, 8000).

5) Резервные копии:
   - Регулярно копируйте файл contracts.db для бэкапа.

6) Вопросы и отладка:
   - Логи сервера появляются в stdout службы NSSM (можно настроить лог-файлы через NSSM).