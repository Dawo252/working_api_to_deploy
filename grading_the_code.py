import time
import pylint.lint
import subprocess
import re
import os
from coverage import Coverage
import pytest

from multiprocessing import Process, Lock, Queue


EXTENSION_PHRASES = {
    ".py": ["try", "except", "finally"],
    ".js": ["try", "catch", "finally"],
    ".java": ["try", "catch", "finally"],
    ".c": ["try", "catch"],
    ".cpp": ["try", "catch"],
    ".h": ["try", "catch"],
    ".cs": ["try", "catch", "finally"],
    ".rb": ["begin", "rescue", "ensure"],
    ".go": ["defer", "recover"],
    ".swift": ["do", "catch"],
    ".php": ["try", "catch"],
    ".r": ["tryCatch"],
    ".ts": ["try", "catch", "finally"],
    ".kt": ["try", "catch", "finally"],
    ".pl": ["eval"],
    ".rs": ["match"],
    ".m": ["@try", "@catch"],
    ".sh": ["try", "catch"],
    ".m": ["try", "catch"],
    ".scala": ["try", "catch", "finally"],
    ".groovy": ["try", "catch", "finally"],
    ".lua": ["pcall", "xpcall"],
    ".jl": ["try", "catch"],
    ".dart": ["try", "catch", "finally"],
    ".ps1": ["try", "catch", "finally"],
    ".vb": ["Try", "Catch", "Finally"],
    ".rkt": ["with-handlers"],
    ".clj": ["try", "catch", "finally"],
    ".ex": ["try", "rescue", "after"],
}
NON_EXTENSION_PHRASES = {
    ".html": [],
    ".css": [],
    ".sql": [],
    ".f": [],
    ".f90": [],
    ".ml": [],
    ".asm": [],
    ".pl": [],
    ".scm": [],
    ".tcl": []
}


class CodeGrader:
    def __init__(self, code_directory_path):  # or code_directory może być po prostu ścieżką do folderu? ewentualnie lista ścieżek do plików/ nazw plików
        self.code_directory_path = code_directory_path
        self.efficiency_score = 0
        self.coverage_score = 0
        self.reliability_score = 0
        self.standarisation_score = 0
        self.vulnerability_score = 0

    def __str__(self):
        return f'efficiency_score: {self.efficiency_score}, coverage_score: {self.coverage_score}, ' \
               f'reliability_score: {self.reliability_score}, standarisation_score: {self.standarisation_score}, ' \
               f'vulnerability_score: {self.vulnerability_score}'

    # ### scores to powinny byc tuple, ale na listach poki co prosciej
    # ### TODO change to tuples ("score_name", value)
    # def update_scores(self, score_list):
    #     if hasattr(self, score_list[0]):
    #         setattr(self, score_list[0], score_list[1])

    @staticmethod
    def map_execution_time_to_score(execution_time):
        # Określ interwały czasu i przypisz ocenę w skali 1-10
        if execution_time < 1:
            return 100
        elif execution_time < 5:
            return 80
        elif execution_time < 10:
            return 60
        elif execution_time < 20:
            return 40
        else:
            return 20


    @staticmethod
    def check_for_design_patterns(file_path):
        with open(file_path, 'r+', encoding="utf-8") as file:
            code = file.read()

    @staticmethod
    def rate_code_reliability(file_path):  # -> pamiętaj, żeby zrobić iterację po folderze
        print("starting rate_code_reliability")
        os.chmod(file_path, 0o777)
        pylint_output = pylint.lint.Run([file_path], do_exit=False)
        pylint_score = None
        reliability_score = None

        if pylint_output.linter.stats:
            pylint_score = pylint_output.linter.stats.global_note
            # reliability_score = pylint_output.linter.stats["global_score"]

        if pylint_score is not None:  #and reliability_score is not None:
            pylint_score = float(pylint_score * 10.0)
            # reliability_score = float(reliability_score)
            print("finishing rate_code_reliability")
            print(f'reliability value added {pylint_score}')
            return pylint_score #, reliability_score
        else:
            print("finishing rate_code_reliability")
            return None  #, None

    def extension(self, file_path):
        print("started the extension")
        with open(file_path, 'r', encoding="latin-1") as file:
            lines = file.readlines()
        code_lines = 0
        lines_with_phrases = 0

        first_bonus = 2

        for line in lines:
            # Pomijamy puste linie oraz linie z samymi znakami białymi
            if line.strip() != '':
                code_lines += 1

            # Sprawdzamy, czy linia zawiera frazę z listy
            for phrase in EXTENSION_PHRASES:
                if str(phrase) in line:
                    lines_with_phrases += 1
                    break  # Kończymy sprawdzanie reszty fraz w tej linii

        # dla kategorii bonus mamy do przyznania
        try:
            if (lines_with_phrases / code_lines) > 0.05:
                first_bonus += 2
                print(f"wyjatki: {lines_with_phrases}")

                if lines_with_phrases > 2:
                    first_bonus += lines_with_phrases - 2 if first_bonus < 10 else 10
        except ZeroDivisionError:
            first_bonus += 0

        secount_bonus = self.coverage_score  # tutaj chciałbym aby był zapis wartości z pokrycia z twojego kodu Dawid z coverage

        bonus = first_bonus + secount_bonus
        print("finishing the extension")
        return bonus

    def coverage_tester(self):
        file_list = os.listdir(self.code_directory_path)

        print("starting coverage_tester")
        index = -1
        try:
            index = file_list.index("tests.py")
        except ValueError:
            pass
        try:
            index = file_list.index("test.py")
        except ValueError:
            pass
        print(index)
        if index != -1:
            tests_url = file_list[index]
        else:
            return 0
        # if "tests.py" or "test.py" not in self.file_list:
        #     self.coverage_score = 0
        # else:
        #     tests_url = self.file_list.index("tests.py")
        try:
            if not os.path.exists(tests_url):
                raise FileNotFoundError(f"The file '{tests_url}' does not exist.")
            else:
                cov = Coverage()
                cov.start()
                pytest.main(['-v', tests_url])
                cov.stop()
                cov.save()
                value = cov.report()
                print("Done.")
        except FileNotFoundError as e:
            return f'file {tests_url} could not be found due to Error: {e}'
        print("finishing coverage_tester")
        self.coverage_score = value
        #return value
        # que_for_results.put("coverage_score", self.coverage_score)

    def evaluate_efficiency(self, file_path):  # -> pamiętaj, żeby zrobić iterację po folderze
        print("starting evaluate_efficiency")
        start_time = time.time()

        # Wykonaj kod z pliku
        # exec(open(file_path, encoding='latin-1').read())

        end_time = time.time()
        execution_time = end_time - start_time

        # efficiency_score = self.map_execution_time_to_score(execution_time)
        print("finishing evaluate_efficiency")
        return 0

    def check_vulnerabilities(self):
        print("starting_vulnerability_checker")
        index = 0
        severity_dict = {'undefined': -1, 'low': -1, 'medium': -1, 'high': -1}
        confidence_dict = {'undefined': -1, 'low': -1, 'medium': -1, 'high': -1}
        # vulnerabilities_dict = {"severity": severity_dict, "confidence": confidence_dict}
        try:
            if not os.path.exists(self.code_directory_path):
                raise FileNotFoundError(f"The file '{self.code_directory_path}' does not exist.")
            else:
                print(f"starting bandit checking {self.code_directory_path}")
                with subprocess.Popen(["bandit", "-r", self.code_directory_path], stdout=subprocess.PIPE) as proc:
                    text = proc.stdout.read()
        except FileNotFoundError as e:
            return f'file {self.code_directory_path} could not be found due to Error: {e}'
        except Exception as e:
            return f'Error: unexpected error occured: {e}'
        text = str(text)
        number_values_from_text = re.findall("[0-9]+", text)
        vulnerabilities_amount = number_values_from_text[-9:-1]

        for key_sev, key_conf in zip(list(severity_dict), list(confidence_dict)):
            if key_sev and key_conf == "high":
                severity_dict[key_sev] = int(vulnerabilities_amount[index])
                confidence_dict[key_conf] = int(vulnerabilities_amount[index + 4])
            index += 1

        self.vulnerability_score = max((100.0 - (sum(severity_dict.values()) + sum(confidence_dict.values()))), 0)
        #TODO: zmienic jakos obliczanie oceny dla vulnerability_score
        # print("finished vulnerability_checker")

    def check_for_documentation(self):
        file_list = os.listdir(self.code_directory_path)
        index = -1
        try:
            index = file_list.index("documentation.py")
        except ValueError:
            pass
        try:
            index = file_list.index("README.py")
        except ValueError:
            pass
        print(index)
        if index != -1:
            documentation_url = file_list[index]
        else:
            return 0
        os.chmod(documentation_url, 0o777)
        with open(documentation_url, 'r+', encoding="utf-8") as file:
            documentation = file.read()
        print(documentation)

    def calculate_code_standardization_score(self, file_path):   # -> pamiętaj, żeby zrobić iterację po folderze
        print("starting calculate_code_standardization_score")
        os.chmod(file_path, 0o777)
        with open(file_path, 'r+', encoding="utf-8") as file:
            # print("started reading the code")
            code = file.read()
            # print("read the code")
        score = 0
        max_score = 80  # Maksymalna liczba punktów za podstawowe kryteria

        # Sprawdzenie zgodności ze standardami
        # (Załóżmy, że standard to nazwy zmiennych pisane snake_case, funkcje PascalCase itp.)
        # print("finding typing cases" + 20 * "*")
        variables_snake_case = re.findall(r'\b[a-z][a-z_0-9]*\b', code)
        variables_pascal_case = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', code)
        # print("found typing cases" + 20 * "*")

        if variables_snake_case and variables_pascal_case:
            score += min(20, len(variables_snake_case) + len(variables_pascal_case))
        # print("calculated typing cases scores" + 20 * "*")
        # Sprawdzenie czy kod jest czytelny
        # (Tutaj można przeprowadzić dodatkową analizę formatowania, wcięć itp.)
        # W tym przykładzie załóżmy, że jeśli kod zawiera odpowiednią ilość wcięć, jest czytelny.
        indentation_count = code.count('\t')
        if indentation_count >= 10:
            score += min(10, indentation_count - 9)  # 1 punkt za każde wcięcie powyżej 9
        # print("scored readibility" + 20 * "*")

        # Sprawdzenie czy kod jest dobrze skomentowany
        # (Załóżmy, że dobrze skomentowany kod zawiera co najmniej 10% komentarzy i +1 punkt za każdą linię komentarza)
        lines_of_code = len(re.findall(r'\n', code)) + 1
        comments = re.findall(r'#', code)
        comments_count = len(comments)
        if comments_count >= 0.1 * lines_of_code:
            score += min(15, comments_count)  # 1 punkt za każdą linię komentarza
        # print("found comments and scored them" + 20 * "*")

        # Sprawdzenie czy kod unika powtórzeń
        # (Tutaj możemy założyć, że unikanie powtórzeń oznacza istnienie funkcji używanej co najmniej 3 razy)
        functions = re.findall(r'def \w+\(', code)
        functions_count = len(functions)
        if functions_count >= 3:
            score += min(10, functions_count - 2)  # 1 punkt za każdą funkcję powyżej 2
        # print("found functions and scored them" + 20 * "*")

        # Sprawdzenie czy kod jest bezpieczny
        # (Tutaj możemy założyć, że kod jest bezpieczny, jeśli nie zawiera oczywistych luk bezpieczeństwa)
        if 'eval(' not in code and 'os.system(' not in code:
            score += 15

        # Sprawdzenie użycia nowoczesnych konstrukcji
        # (Załóżmy, że używanie list comprehension i async/await zwiększa ocenę)
        if 'async' in code and '[[' not in code and 'for ' not in code:
            score += 10

        score += self.extension(file_path)

        # Ograniczenie wyniku do przedziału 1-80 dla podstawowych kryteriów
        score = max(1, min(score, max_score))

        # Ograniczenie wyniku do przedziału 1-100 (łącznie 100 punktów za wszystkie kryteria)
        score = max(1, min(score, 100))

        # print("finishing calculate_code_standardization_score")

        return score

    def run_single_file_tests(self):
        print("starting run_single_file_tests")
        file_list = os.listdir(self.code_directory_path)
        print(file_list)
        # file_path_prefix = self.code_directory_path + "/"
        effeciency_score_sum = 0
        reliability_score_sum = 0
        standarisation_score_sum = 0
        if len(file_list) != 0:
            divider = len(file_list)
        else:
            divider = 1
        prefix = self.code_directory_path
        for file_name in file_list:
            print(file_name)
            effeciency_score_sum += self.evaluate_efficiency(prefix + f'/{file_name}')
            # reliability_score_sum += self.rate_code_reliability(prefix + f'/{file_name}')
            standarisation_score_sum += self.calculate_code_standardization_score(prefix + f'/{file_name}')

        self.efficiency_score = effeciency_score_sum/divider
        self.reliability_score = reliability_score_sum/divider
        self.standarisation_score = standarisation_score_sum/divider
        # print("finishing run_single_file_tests")

""" metody, które wykonują się na całym folderze zostaw jako metody funkcji, a jeśli działają na pojedynczym pliku
    to zrób je statyczne i potem zrób jedną metodę klasy która je wszystkie na pętli wykona"""
