import PyInstaller.__main__
import os
import shutil


def build():
    print("Building Acanthophis executable...")

    # Clean previous builds
    if os.path.exists("build"):
        shutil.rmtree("build")
    # if os.path.exists("dist"):
    #     shutil.rmtree("dist")

    PyInstaller.__main__.run(
        [
            "acanthophis/main.py",
            "--name=acanthophis",
            "--onefile",
            "--clean",
            "--paths=acanthophis",  # Add acanthophis directory to search path
        ]
    )


if __name__ == "__main__":
    build()
