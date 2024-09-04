from typing import List


# todo: написать ревьюеру после отправки работы, что тут такие странные значения по умолчанию, так как
#  иначе не продут тесты. В тестах респонс это одна структура данных, а в примере из доки другая структура данных
class HomeworkDTO:
    def __init__(self,
                 status: str,
                 homework_name: str,
                 id: int = 0,
                 reviewer_comment: str = '',
                 date_updated: str = '',
                 lesson_name: str = ''):

        self._id = id
        self._status = status
        self._homework_name = homework_name
        self._reviewer_comment = reviewer_comment
        self._date_updated = date_updated
        self._lesson_name = lesson_name

    @property
    def id(self):
        return self._id

    @property
    def status(self):
        return self._status

    @property
    def homework_name(self):
        return self._homework_name

    @property
    def reviewer_comment(self):
        return self._reviewer_comment

    @property
    def date_updated(self):
        return self._date_updated

    @property
    def lesson_name(self):
        return self._lesson_name

    def __dict__(self):
        return {
            'id': self._id,
            'status': self._status,
            'homework_name': self._homework_name,
            'reviewer_comment': self._reviewer_comment,
            'date_updated': self._date_updated,
            'lesson_name': self._lesson_name
        }


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
