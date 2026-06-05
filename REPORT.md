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

# Отчет о профилировании

## app/services/services -  JournalService.get_complete_journal

###### Описание

Профилируемая функция используется для запроса к БД, получение из нее данных и дальнейшего создания объекта Journal. Сложность работы состоит в том, что для создания Journal необходимо множество данных, хранимых в связанных таблицах: workouts, trains, sets, rows, routes, exercises. В первой версии функции использованы множественные вызовы подкатегорий (для каждого rows свои routes и т.п.), что создало проблему N + 1. Решено было объединить запросы и сократить до шести: выбор журнала (table journals), выбор всех workouts для журнала, выбор всех trains для workouts и т.д. Затем происходит сортировка по id и сбор Journal.

Согласно отчету, значительное время занимает работа асинхронного цикла событий и ожидание I/O-операций. Из прочего, затратным вышло создание доменных моделей (Route, Exercise, и т.д.) — в связи с проверками re.fullmatch и наличием __post_inint__ практически в каждом классе.

###### Предложения по улучшению

Пересмотреть создание доменных моделей и убрать излишние провеки в __post_init__, добавить re.compile() для типичных регулярных выражений. Пересмотреть SQL-запросы на возможность объединения. Убрать промежуточные преобразования данных между БД и доменными объектами (которые в примере ниже были созданы 36_000 раз).

###### Вырезка из отчета cProfile (запуск функции 10_000 раз)

ncalls  tottime  percall  cumtime  percall filename:lineno(function)
14006    0.015    0.000    1.090    0.000 profiling/profile_get_journal.py:11(scenario)
15000    0.016    0.000    1.074    0.000 app\services\services.py:85(get_complete_journal)
15000    0.296    0.000    1.058    0.000 app\infrastructure\database\repo.py:158(get_journal_full)
36000    0.054    0.000    0.161    0.000 app\domain\models.py:340(__post_init__)

## app/services/parser.py — JournalParser.parse_rows (training_category=TrainingCategory.CLIMBING)

###### Описание

Профилируемая функция используется для парсинга текста сообщения с подходами (в данном случае, скалолазные трассы). Из отчета видно, что значительную часть работы (около 70% времени) занимает функция get_route, которая отвечает за распознование и формирование Route. Также re.compile, re.fullmatch в сумме занимают примерно 57% времени, что в значительной степени обусловлено количеством вызовов (1_000_000 в данном случае). Работа с доменными объектами занимает примерно 70% времени — именно там, в __post_init__ вызываются методы модуля re и валидация.

###### Предложения по улучшению

Скомпилировать паттерн регулярного выражения для идентификации Route заранее! Пересмотреть метод __post_init__ на исбыточную валидацию данных.

###### Вырезка из отчета cProfile

ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    1    0.000    0.000    7.490    7.490 app\services\parser.py:16(parse_rows)
    1    1.054    1.054    7.490    7.490 app\services\parser.py:104(_parse_rows_climbing)
500000    1.358    0.000    5.699    0.000 app\services\parser.py:43(get_route)
500000    0.793    0.000    3.040    0.000 <string>:2(__init__)
1000000    0.761    0.000    2.543    0.000 ...\Lib\re\__init__.py:169(fullmatch)
500000    0.768    0.000    2.247    0.000 app\domain\models.py:340(__post_init__)
1000006    0.690    0.000    0.950    0.000 ...\Lib\re\__init__.py:330(_compile)
1000000    0.837    0.000    0.837    0.000 {method 'fullmatch' of 're.Pattern' objects}
2702306    0.525    0.000    0.525    0.000 {built-in method builtins.isinstance}
100000    0.184    0.000    0.217    0.000 app\domain\models.py:312(__post_init__)

## app/services/parser.py — JournalParser.parse_rows (training_category=TrainingCategory.GYM)

###### Описание

Из отчета cProfile видно, что функция отрабатывает в разы быстрее, чем аналог для скалолазных тренировок. Разница более, чем в 100 раз. При этом, временные затраты непосредственно на обработку текста минимальные, так же как и на создание доменных моделей.

###### Предложения по улучшению

Считаю, что функция работает оптимально, дальнейшее усовершенствование излишне.

###### Вырезка из отчета cProfile

ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    1    0.000    0.000    0.008    0.008 C:\Users\ARINA\PyProjects\climbing-diary-tg-bot\app\services\parser.py:16(parse_rows)
    1    0.002    0.002    0.008    0.008 C:\Users\ARINA\PyProjects\climbing-diary-tg-bot\app\services\parser.py:72(_parse_rows_gym)
