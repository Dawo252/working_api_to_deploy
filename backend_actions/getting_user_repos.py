from github import Github
import os, stat
import shutil
import git
import openai
from pathlib import Path
# from toolz import partition
from multiprocessing import Process, Lock, Queue


openai.api_key = "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"


language_extensions = {
    "Python": [".py"],
    "JavaScript": [".js"],
    "Java": [".java"],
    "C": [".c"],
    "C++": [".cpp", ".h"],
    "C#": [".cs"],
    "Ruby": [".rb"],
    "Go": [".go"],
    "Swift": [".swift"],
    "PHP": [".php"],
    "R": [".r"],
    "TypeScript": [".ts"],
    "Kotlin": [".kt"],
    "Perl": [".pl"],
    "Rust": [".rs"],
    "Objective-C": [".m"],
    "Shell": [".sh"],
    # "HTML": [".html"],
    # "CSS": [".css"],
    "SQL": [".sql"],
    "MATLAB": [".m"],
    "Scala": [".scala"],
    "Groovy": [".groovy"],
    "Lua": [".lua"],
    "Haskell": [".hs"],
    "Julia": [".jl"],
    "Dart": [".dart"],
    "PowerShell": [".ps1"],
    "VB.NET": [".vb"],
    "Racket": [".rkt"],
    "Clojure": [".clj"],
    "Elixir": [".ex"],
    "Fortran": [".f", ".f90"],
    "OCaml": [".ml"],
    "Assembly": [".asm"],
    "Prolog": [".pl"],
    "Scheme": [".scm"],
    "Tcl": [".tcl"]
}


class GetUserRepos:
    def __init__(self, main_directory, folder_core_name, repo_paths_list=None, repo_names_list=None):
        self.main_directory = main_directory
        self.folder_core_name = folder_core_name
        if main_directory is not None:
            number_of_directories = 0
            list_of_direcories_indexes = []
            directory_list = os.listdir(f"{main_directory}")
            for directory in directory_list:
                list_of_direcories_indexes.append(int(directory[6:]))
            if len(list_of_direcories_indexes) > 0:
                number_of_directories = max(list_of_direcories_indexes)
            self._number_of_directories = number_of_directories
            self.first_directory = f"{self.main_directory}/{folder_core_name}{self._number_of_directories + 1}"
            self.reorganized_directory = f"{self.main_directory}/{folder_core_name}{self._number_of_directories + 2}"
        if repo_paths_list is None:
            self.repo_paths_list = set()
        if repo_names_list is None:
            self.repo_names_list = set()

    def get_github_repo_names(self, access_token):
        # Twój GitHub Access Toke

        # Utwórz obiekt klasy Github z odpowiednimi uprawnieniami
        github = Github(login_or_token=access_token)

        # Pobierz informacje o użytkowniku (np. twój użytkownik)
        user = github.get_user()

        # Wyświetl listę publicznych repozytoriów
        for repo in user.get_repos():
            url = f"https://{access_token}@github.com/" + repo.full_name
            self.repo_names_list.add(repo.full_name)
            self.repo_paths_list.add(url)

        # Wyświetl listę prywatnych repozytoriów
        # Tutaj dodamy potem checkbox na dostęp do prywatnych repo
        for repo in user.get_repos(visibility="private"):
            url = f"https://{access_token}@github.com/" + repo.full_name
            self.repo_names_list.add(repo.full_name)
            self.repo_paths_list.add(
                url)

    @staticmethod
    def clone_repository(repo_url, directory):
        if repo_url is not None:
            try:
                os.system(f'sudo git clone --filter=blob:none --depth 1 {repo_url} {directory} ')
                print("done downloading")
            except git.exc.InvalidGitRepositoryError:
                print("no repo")
        else:
            print("no github_repo to download")

    def clone_repositories(self):
        for repo in self.repo_paths_list:
            self.clone_repository(repo, self.first_directory + f"/{repo.split('.com/', 1)[1]}")

    def reorganize_repository(self):
        index_of_the_main_folder = None
        if not os.path.exists(self.reorganized_directory):
            os.system(f"sudo mkdir {self.reorganized_directory}")
        os.system(f"sudo chmod 777 {self.first_directory} {self.reorganized_directory}")
        for root, _, files in os.walk(self.first_directory):
            for filename in files:
                root = root.replace("\\", "/")
                file_path = root + f'/{filename}'
                file_path_list = file_path.split("/")
                if index_of_the_main_folder is None:
                    index_of_the_main_folder = file_path_list.index(f"{self.folder_core_name}"
                                                                    f"{self._number_of_directories + 1}")
                if not (Path.cwd() / self.reorganized_directory / file_path_list[index_of_the_main_folder + 2]).exists():
                    os.mkdir(self.reorganized_directory + f'/{file_path_list[index_of_the_main_folder + 2]}')
                new_file_path = self.reorganized_directory + f'/{file_path_list[index_of_the_main_folder + 2]}' + \
                                f'/{filename}'
                os.system(f'sudo chmod -R 777 {self.first_directory}')
                os.system(f'sudo chmod -R 777 {self.reorganized_directory}')
                shutil.move(file_path, new_file_path)
        print("moved shit out")

    def remove_files_with_other_extensions(self):
        os.system(f'sudo chmod -R 777 {self.first_directory}')
        os.system(f'sudo chmod -R 777 {self.reorganized_directory}')
        for root, _, files in os.walk(self.first_directory):
            for filename in files:
                filename2 = filename.replace("\\", "/")
                root = root.replace("\\", "/")
                file_path = root + f'/{filename2}'
                file_extension = os.path.splitext(filename2)[1]
                if file_extension.lower() not in [ext.lower() for exts in language_extensions.values() for ext in exts]:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
