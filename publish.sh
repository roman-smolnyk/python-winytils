#!/usr/bin/env bash
git push origin main
git push origin_github main

git tag -a v0.0.4 -m "v0.0.4"
git push origin v0.0.4
git push origin_github v0.0.4

python -m build
python -m twine upload dist/*
rm -rf dist
