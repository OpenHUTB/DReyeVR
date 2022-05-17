#!/usr/bin/env python

import os
from typing import List, Optional

from utils import (
    CARLA_PATH_FILE,
    SR_PATH_FILE,
    SUPPORTED_CARLA,
    SUPPORTED_SCENARIO_RUNNER,
    advanced_join,
    default_args,
    expand_correspondences_glob,
    generate_correspondences,
    get_leaf_from_path,
    print_line,
    print_status,
    verify_installation,
    verify_version,
)

DOC_STRING = "Simple script to check correspondences are present"


def check_repo(
    ROOT: str = None,
    corr_file: str = CARLA_PATH_FILE,
    verify_files: List[str] = [],
    git_tag: Optional[str] = None,
    verbose: Optional[bool] = True,
) -> bool:
    if ROOT is None:
        return True
    # begin check process
    ROOT = os.path.abspath(ROOT)  # convert to absolute path
    verify_installation(ROOT, verify_files)
    if verify_version(ROOT, git_tag) == False:
        return True
    print_line()
    print(f"Checking root ({ROOT})")

    corr = generate_correspondences(corr_file)
    all_corr = expand_correspondences_glob(corr)

    missing_files: List[str] = []
    for k in all_corr.keys():
        leafname = get_leaf_from_path(k)
        expected_path: str = advanced_join([ROOT, all_corr[k], leafname])
        if os.path.exists(expected_path):
            if verbose:
                print(f"{expected_path} -- found")
        else:
            if verbose:
                print(f"{expected_path} -- not found")
            missing_files.append(expected_path)
            # raise Exception(f"Failed to find {expected_path}")

    if len(missing_files) > 0:
        print()
        print("ERROR: the following files are missing:")
        for m in missing_files:
            print(m)
        return False

    print("Success!")
    return True


if __name__ == "__main__":
    args = default_args(
        DOC_STRING,
        other_args=[
            {"name": "--verbose", "action": "store_true"},
            {"name": "--hard", "action": "store_true"},
        ],
    )

    print_line()
    check_carla = check_repo(
        args.carla,
        corr_file=CARLA_PATH_FILE,
        git_tag=SUPPORTED_CARLA,
        verify_files=["CHANGELOG.md"],
        verbose=args.verbose,
    )
    print()
    check_sr = check_repo(
        args.scenario_runner,
        corr_file=SR_PATH_FILE,
        git_tag=SUPPORTED_SCENARIO_RUNNER,
        verify_files=["scenario_runner.py"],
        verbose=args.verbose,
    )

    print()

    print_line()
    print(f"Summary:")
    if args.carla:
        print(f"Carla          [{print_status(check_carla)}]")
    if args.scenario_runner:
        print(f"ScenarioRunner [{print_status(check_sr)}]")

    print()
    print("Done check")
    print_line()
