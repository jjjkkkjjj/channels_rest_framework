rm -rf ../docs/* _build/html/
sphinx-apidoc -f -o ./source ../channels_rest_framework
make html
cp -ar _build/html/. ../docs/