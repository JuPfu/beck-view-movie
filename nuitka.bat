del /Q /S /F main.build main.dist main.onefile-build
python -m nuitka --standalone --onefile --windows-icon-from-ico=beck-view-movie.png -o "beck-view-movie" main.py