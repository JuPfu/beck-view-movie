rm -rx build dist
rm -rf *.c *.so
python setup.py build_ext --inplace
mkdir -p dist
mv *.so dist/
pyinstaller beck-view-movie.spec --noconfirm
mv dist/beck-view-movie .
dir=$(pwd -P)
echo 'Executable `beck-view-digitize` ready for usage in directory' $dir