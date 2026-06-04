# Отчет покрытия тестов

### Использованные инструменты

asyncio-1.4.0, cov-7.1.0, mock-3.15.1

### Покрытие

Name                                                      Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------
app\bot\handlers\__init__.py                                  5      0   100%
app\bot\handlers\commands.py                                 38      0   100%
app\bot\handlers\exceptions.py                               14      5    64%   4, 9, 14, 18, 21
app\bot\handlers\journal_handlers\add_workout.py            124     84    32%   53-55, 75-88, 99-108, 115-120, 128-135, 143-144, 153-164, 172-186, 192-211, 217-221, 236-255, 263-269
app\bot\handlers\journal_handlers\journal_operations.py      37     16    57%   44-50, 62-79
app\bot\handlers\journal_handlers\validators.py              12      8    33%   7-10, 13-23
app\bot\keyboards\journal_keyboards.py                       23      6    74%   68, 77-82
app\bot\states\add_workout.py                                15      0   100%
app\bot\states\get_journal.py                                 7      0   100%
app\domain\enums.py                                           9      0   100%
app\domain\exceptions.py                                     12      3    75%   3-4, 7
app\domain\models.py                                        219     29    87%   85-90, 94-98, 111-112, 126-136, 218, 256, 263-264, 274-278
app\infrastructure\database\__init__.py                       4      0   100%
app\infrastructure\database\create_tables.py                  7      4    43%   26-29
app\infrastructure\database\database.py                      29     15    48%   15, 24-28, 36-37, 45-46, 53, 56-57, 65-68
app\infrastructure\database\repo.py                          95     63    34%   74-134, 142-149, 153-157, 161-221
app\infrastructure\database\sql_models.py                    28      0   100%
app\lexic\ru.py                                              13      0   100%
app\lexic\ru_kboards.py                                       5      0   100%
app\services\parser.py                                       74      0   100%
app\services\services.py                                     51      0   100%
---------------------------------------------------------------------------------------
TOTAL                                                       821    233    72%

### Описание

Всего тестов: 113. Покрыты тестами модули: domain, database, services, lexic, states.

Среди непокрытых частей модулей:
    app/domain/models.py — классы, относящиеся к представлению данных их БД;
    app/infrastructure/database/repo.py — функции, записывающие/читающие данные БД;
    app/infrastructure/database/database.py — непосредственно SQL-запросы.

Среди прочего не покрыты тестами:
    Функции, требующие интеграционного тестирования;
    Модули, относящиеся к aiogram: handlers, middleware.

![alt text](<coverage_report.png>)
