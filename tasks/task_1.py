from celery_app.utils import create_celery
from core.config import get_settings
from backend_actions.getting_user_repos import GetUserRepos
from backend_actions.grading_the_code import CodeGrader
import os, shutil

settings = get_settings()

celery = create_celery()

@celery.task(name="task_1", bind=True, max_retries=3, default_retry_delay=10, queue="user_github_que2") #  ack_late=True, jesli chcemy od razu usuwac po odczytaniu wiadomosci z que
def task_1(self, **kwargs):  # change get user repos to be linear -> done
    github_something = GetUserRepos(kwargs["folder"])
    github_something.get_github_repo_names(access_token=kwargs["access_token"])
    print(github_something.repo_names_list)
    print(github_something.repo_paths_list)
    github_something.clone_repositories()
    github_something.remove_files_with_other_extensions()
    github_something.reorganize_repository(kwargs["folder"], f"{kwargs['folder']}2")

    folder = kwargs["folder"] + "2"
    dir_dict = os.listdir(folder)
    grade_dict = {}
    for repo in dir_dict:
        temp_dict = {}
        code = CodeGrader(f"{folder}/{repo}")
        code.coverage_tester()
        code.check_vulnerabilities()
        code.run_single_file_tests()
        temp_dict["coverage_score"] = code.coverage_score
        temp_dict["vulnerability_score"] = code.vulnerability_score
        temp_dict["efficiency_score"] = code.efficiency_score
        temp_dict["reliability_score"] = code.reliability_score
        temp_dict["standarisation_score"] = code.standarisation_score
        grade_dict[repo] = temp_dict
        print('one done')

    os.system(f"sudo rm -rf {kwargs['folder'] + '2'}")
    os.system(f"sudo rm -rf {kwargs['folder']}")
    os.system(f"sudo mkdir {kwargs['folder']}")
    os.system(f"sudo mkdir {kwargs['folder'] + '2'}")
    os.system(f"sudo chmod 777 {kwargs['folder']} {kwargs['folder']}2")
    print("done and ready for next")

    return grade_dict

