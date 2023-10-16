from celery_app.utils import create_celery
from core.config import get_settings
from getting_user_repos import GetUserRepos
from grading_the_code import CodeGrader
import os, shutil

settings = get_settings()

celery = create_celery()

@celery.task(name="task_1", bind=True, max_retries=3, default_retry_delay=10, queue="user_github_que2") #  ack_late=True, jesli chcemy od razu usuwac po odczytaniu wiadomosci z que
def task_1(self, **kwargs):  # change get user repos to be linear -> done
    github_something = GetUserRepos("/home/dawo252/tests/testtt")
    github_something.get_github_repo_names(access_token=kwargs["access_token"])
    print(github_something.repo_names_list)
    print(github_something.repo_paths_list)
    github_something.clone_repositories()
    github_something.reorganize_repository(f"/home/dawo252/tests/testtt",
                                           "/home/dawo252/tests/testtt2")
    github_something.remove_files_with_other_extensions()

    folder = "/home/dawo252/tests/testtt2"
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

    print(grade_dict)
    for each in os.listdir("/home/dawo252/tests"):
        if each.startswith("testtt") and each != "testtt2":
            for root, dirs, files in os.walk(f"/home/dawo252/tests/{each}"):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))

    for root, dirs, files in os.walk("/home/dawo252/tests/testtt2"):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

    return grade_dict

