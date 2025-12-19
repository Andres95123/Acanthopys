import PyInstaller.__main__
import os
import shutil


def build():
    print("Building Acanthophis REPL executable...")

    # Clean previous builds
    if os.path.exists("build_repl"):
        shutil.rmtree("build_repl")
    # We can output to dist as well, maybe dist/repl.exe

    PyInstaller.__main__.run(
        [
            "repl/repl.py",
            "--name=repl",
            "--onefile",
            "--clean",
            "--distpath=dist",
            "--workpath=build_repl",
            # We don't need to bundle acanthophis source if repl uses the exe.
            # But repl imports 'acanthophis.parser' in my previous version?
            # No, I removed that dependency in repl.py.
            # So it should be standalone.
        ]
    )


if __name__ == "__main__":
    build()
