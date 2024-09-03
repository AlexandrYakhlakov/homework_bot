from dataclasses import dataclass
from typing import List, Optional


# todo: написать ревьюеру после отправки работы, что тут такие странные значения по умолчанию, так как
#  иначе не продут тесты. В тестах респонс это одна структура данных, а в примере из доки другая структура данных
class HomeworkDTO:
    def __init__(self,
                 id = '',
                 status = '',
                 homework_name = '',
                 reviewer_comment = '',
                 date_updated = '',
                 lesson_name = ''):
        self.id = id
        self.status = status
        self.homework_name = homework_name
        self.reviewer_comment = reviewer_comment
        self.date_updated = date_updated
        self.lesson_name = lesson_name


class HomeworkStatusesDTO:
    def __init__(self,
                 homeworks: List[HomeworkDTO],
                 current_date: int):
        self._homeworks = homeworks.copy()
        self._parse_homeworks()
        self._current_date = current_date
        self._current_date_validate()

    @property
    def homeworks(self):
        return self._homeworks

    @property
    def current_date(self):
        return self._current_date

    def _parse_homeworks(self):
        if not isinstance(self._homeworks, list):
            raise TypeError('Ошибка валидации HomeworkStatusesDTO.homeworks не list')

        parse_homeworks = []
        for item in self._homeworks:
            if not isinstance(item, dict):
                raise TypeError('Ошибка валидации HomeworkStatusesDTO.homeworks[] не dict')
            parse_homeworks.append(HomeworkDTO(**item))
        self._homeworks = parse_homeworks

    def _current_date_validate(self):
        if not isinstance(self.current_date, int) or self.current_date < 0:
            raise ValueError('Ошибка валидации current_date значение должно быть целочисленным и больше 0')
