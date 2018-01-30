#/bin/bash

docker build -t pager2-base -f base.docker .;
docker build -t pager2-build -f build.docker .;

mkdir -p wheelhouse

docker run --rm \
       -v "$(pwd)":/application \
       -v "$(pwd)"/wheelhouse:/wheelhouse \
       pager2-build

docker build -t pager2-run -f run.docker .;

echo "If there were no errors in the previous commands,"
echo "you can now run your application with the following command:"
echo "  docker run --rm -it -p 8080:8080 -v \"$(pwd)\"/pager-data:/pager-data pager2-run"
