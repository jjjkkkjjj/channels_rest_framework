rm -rf ../docs/* _build/html/
sphinx-apidoc -f -o ./source ../rest_framework_channels
make html
cp -ar _build/html/. ../docs/