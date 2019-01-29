# -*- coding: utf-8 -*-
"""
DNS domain searcher

Приложение по поиску адресов фишинговых сайтов.
На вход требуется подать одно или несколько 
слов. Программа модифицирует их по 4 алгоритмам,
преобразует в домены в заданных доменных зонах и
постарается найти адреса этих доменов.

Использование:
>>>python3 dns_searcher.py word1 word2 ... wordN

Github: github.com/oleggr/another_one_resolver
"""

# TODO хотя бы ссылку на github в шапке добавил
# TODO почему называется main.py ?
# TODO пример использования в шапке а не в DomainNameSearcher (но и там можно оставить)!

import sys
# TODO нигде не исользуется. Рудимент. Зачем это? (про import time)
import string
import datetime
import threading

from prettytable import PrettyTable
import dns.resolver


__author__ = 'oleggr'
__email__ = 'oleg.gr@outlook.com'


# TODO если ни от кого не наследуется убери (). В Python3 так не пишут
class DomainNameSearcher:
    # TODO в docstring-ах нужно везде использовать """ вместо ''' ! (ИСПРАВЛЕНО)
    """
    Приложение по поиску адресов фишинговых сайтов.
    На вход требуется подать одно или несколько 
    # слов. Программа модифицирует их по 4 алгоритмам,
    преобразует в домены в заданных доменных зонах и
    постарается найти адреса этих доменов.

    Использование:
    >>>python3 dns_searcher.py word1 word2 ... wordN
    """

    ZONES = [ 
            'com', 'ru', 'net', 'org', 'info', 'cn', 'es', 
            'top', 'au', 'pl', 'it', 'uk', 'tk', 'ml', 'ga',
            'cf', 'us', 'xyz', 'top', 'site', 'win', 'bid'
        ]

    DATA_FORMAT = '%H.%M.%S-%d.%m.%Y'

    def __init__(self):

        self.report = dict()

    # TODO зачем self если он не используется? Сделать все эти функции статическими.
    
    @staticmethod
    def _argument_parser():
        """
        Функция, которая занимается обработкой входных
        параметров
        :return: Список слов
        """

        res = []

        for elem in sys.argv[1:]:
            if not elem in res:
                res.append(elem)

        return res

    def _get_extended_word_set(self, word_set):
        """
        Функция, модифицирующая входной набор слов
        по 4 различным стратегиям
        :param word_set: Поданный на вход набор слов
        :return: Список модифицированных слов
        """

        res = []
        res.extend(word_set)

        for word in word_set:

            # TODO нарушение PEP8 -- пробел после # должен быть!

            res.extend(self._letter_adder(word))
            res.extend(self._symbol_changer(word))
            res.extend(self._point_adder(word))
            res.extend(self._symbol_remover(word))
            pass

        return res

    @staticmethod
    def _letter_adder(word):
        """
        Стратегия изменения слова, добавлением в 
        конец одной дополнительной буквы
        :param word: str - Немодифицированное слово
        :return: Список модифицированных слов, 
        полученных из исходного
        """

        modified_word = []

        # string.ascii_lowercase - все английские буквы

        for letter in string.ascii_lowercase:
            tmp = word + letter
            modified_word.append(tmp)

        return modified_word

    @staticmethod
    def _symbol_changer(word):
        """
        Стратегия изменения слова, заменой одной
        буквы на другую, схожую по внешнему виду
        :param word: str - Немодифицированное слово
        :return: Список модифицированных слов, 
        полученных из исходного
        """

        modified_word = []

        # Открываем укороченный файл со списком гомоглифов
        # В случае необходимости можно произвоить чтение 
        # из полного файла

        # with open('homoglyph.txt', 'r') as f:
        with open('homoglyph_short.txt', 'r') as f:

            # Производим чтение файла, согласно его структуре

            for line in f:
                tmp_line = line.split(':')

                for i in range(0, len(word)):

                    # Если какая-то буква в слове имеет гомоглиф
                    # производится ее замена на каждый из
                    # возможных гомоглифов

                    # В данной реализации получаются модификации
                    # слова, где заменена только одна буква

                    if word[i] == tmp_line[0]:

                        for b in tmp_line[1].split():
                            tmp_word = word[0:i] + b + word[i+1:len(word)]

                            # Здесь и далее в коде программы таким
                            # образом производится проверка на повтор
                            # измененного слова

                            if not tmp_word in modified_word:
                                modified_word.append(tmp_word)

        return modified_word

    @staticmethod
    def _point_adder(word):
        """
        Стратегия изменения слова, выделением поддомена
        :param word: str - Немодифицированное слово
        :return: Список модифицированных слов, 
        полученных из исходного
        """

        modified_word = []

        for i in range(1, len(word)):

            # Если символы слева и справа буквы, между
            # ними можно поставить точку

            if (word[i - 1] in string.ascii_letters) \
                    and (word[i] in string.ascii_letters):

                tmp = word[0:i] + '.' + word[i:len(word)]

                modified_word.append(tmp)

        return modified_word

    @staticmethod
    def _symbol_remover(word):
        """
        Стратегия изменения слова, удалением одной буквы
        :param word: str - Немодифицированное слово
        :return: Список модифицированных слов, 
        полученных из исходного
        """

        modified_word = []
        tmp = word

        # Проходя по слову, удаляем одну букву и заносим
        # модифицированное слово в список

        for i in range(0, len(word)):
            tmp = word[0:i] + word[i+1:len(word)]

            # TODO конструкция not in предпочтительнее (ИСПРАВЛЕНО)
            # if not tmp in modified_word:
            if tmp not in modified_word:
                modified_word.append(tmp)

        return modified_word

    def _domain_zone_adder(self, extended_word_set):
        """
        Функция для составления доменов из списка
        измененных слов
        :param extended_word_set: Расширенный список
        слов (немодифицированных и модифицированных)
        :return: Список доменов
        """

        # TODO здесь неудобно их править! Вынести в глобальные переменные!
        # zones = [ 
        #     'com', 'ru', 'net', 'org', 'info', 'cn', 'es', 
        #     'top', 'au', 'pl', 'it', 'uk', 'tk', 'ml', 'ga',
        #     'cf', 'us', 'xyz', 'top', 'site', 'win', 'bid'
        # ]

        urls = []

        for word in extended_word_set:
            for zone in self.ZONES:
                url = word + '.' + zone
                urls.append(url)

        return urls

    def _multithread_dns_resolve(self, urls):
        """
        Функция для многопотокового выполнения
        dns-запросов
        :param urls: Список доменов
        """

        threads_num = 6
        threads = []

        for i in range(threads_num):

            t = threading.Thread(
                    target=self._thread_run, 
                    args=(i, urls, threads_num)
                )

            t.start()

            threads.append(t)

        for t in threads:
            t.join()

    def _thread_run(self, thread_index, urls, threads_num):
        """
        Функция одного потока
        :param thread_index: Индекс потока
        :param urls: Список доменов
        :param threads_num: Количество потоков
        """

        while thread_index < len(urls):
            url = urls[thread_index]
            
            record = self._resolve_dns(url)

            print('{:<20}{}'.format(url, record))
            
            if len(record):
                self.report[url] = record

            thread_index += threads_num

    @staticmethod
    def _resolve_dns(url):
        """
        Получение dns-записи по данному домену
        :param url: Домен
        :return dns_records: Лист адресов этого домена
        """

        dns_records = []

        try:
            dns_results = dns.resolver.query(url)
            dns_records = [ip.address for ip in dns_results]

        except dns.resolver.NXDOMAIN as e:
            # Домен не существует, список адресов домена пустой
            print('EXEPTION:: domain {} not exist'.format(url))

        except dns.resolver.NoAnswer as e:
            # Ответа нет - список адресов домена пустой
            print('EXCEPTION:: {}'.format(e))
            
        except Exception as e:
            # TODO ошибка затеряется в общем потоке ошибок, выводимые в консоль. Если даже и не писать логер, то по какому-либо ключевому слову нужно находить
            # Например так:
            # print("EXCEPTION::"", e)
            print('EXCEPTION:: {}'.format(e))

        return dns_records

    def _get_result(self):
        """
        Функция получения результатов работы программы
        в красивом виде
        :return: Таблица типа  PrettyTable
        """

        '''
        counter = 0

        # TODO:: from prettytable import PrettyTable. Аналогично в _report_to_file_human_readable(...)
        print('{:<5}{:<20}{}'.format('n', 'domain', 'address'))
        print('====|===================|===================')

        for key in self.report:
            counter += 1
            print('{:<5}{:<20}{}'.format(counter, key, str(self.report[key])))
        '''

        x = PrettyTable(['n', 'domain', 'address'])

        counter = 0

        for key in self.report:
            counter += 1

            x.add_row([counter, key, str(self.report[key][0])])

            for i in range(1, len(self.report[key])):

                x.add_row(['', '', str(self.report[key][i])])

        return x

    def _report_to_file(self):
        """
        Функция записи в файл результатов работы программы
        в удобном для последующего парсинга виде
        """

        b = datetime.datetime.now().strftime(self.DATA_FORMAT)

        filename = 'report-{}.txt'.format(b)

        with open(filename, 'w') as f:
            for key in self.report:
                f.write('{}*{}\n'.format(key, str(self.report[key])))

    def _report_to_file_human_readable(self):
        """
        Функция записи в файл результатов работы программы
        в удобном для чтения человеком виде
        """

        # TODO что за @##%(%& !! Вынести в глобальные переменные!
        # import datetime

        # TODO второй раз вижу '%H.%M.%S-%d.%m.%Y' -- вынести в DATA_FORMAT = '%H.%M.%S-%d.%m.%Y' в глобальные переменные
        
        b = datetime.datetime.now().strftime(self.DATA_FORMAT)

        # TODO нужно так:
        # filename = 'report-{}_human_readable.txt'.format(b)

        filename = 'report-{}_human_readable.txt'.format(b)

        # TODO и зачем вообще "human_readable"? В питоне все по умолчанию human readable !

        with open(filename, 'w') as f:
            f.write(str(self._get_result()))
            

    def run(self):
        """
        Основная функция программы, выполняющая запуск всех
        необходимых функций в нужном порядке
        """

        # TODO нет в __init__ self.report=None.
        # self.report = {}

        # Парсинг аргуменов и составление первичного списка слов
        word_set = self._argument_parser()

        # Составление расширенного списка слов
        extended_word_set = self._get_extended_word_set(word_set)
        
        # Получение списка доменов из расширенного спика слов
        urls = self._domain_zone_adder(extended_word_set)
        
        # Многопоточное выполнение dns-запросов по доменам из списка
        self._multithread_dns_resolve(urls)

        # Вывод результата на экран и в файлы
        print(self._get_result())
        self._report_to_file()
        self._report_to_file_human_readable()


if __name__ == '__main__':
    a = DomainNameSearcher()
    a.run()
