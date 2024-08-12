sphinx-apidoc -f -o ./source ../
make html
cp -r _build/html/* ../docs/