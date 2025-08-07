rmdir build
rmdir dist
del *.c *.pyd
python setup.py build_ext --inplace
mkdir dist
move build\lib.win-amd64-cpython-313\*.pyd dist
pyinstaller beck-view-movie.spec --noconfirm
move /y dist\beck-view-movie-bundle\beck-view-movie.exe .
echo "Executable `beck-view-movie.exe` ready for use in %CD%"
