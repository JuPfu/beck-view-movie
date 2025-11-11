rmdir /S /Q build
rmdir /S /Q dist
del *.c
del *.pyd
python setup.py build_ext --inplace
mkdir dist
move *.pyd dist
pyinstaller beck-view-movie.spec --noconfirm
copy /Y dist\beck-view-movie.exe "%CD%""
echo "Executable `beck-view-movie.exe` ready for usage in directory %CD%"