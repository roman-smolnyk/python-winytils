#!/usr/bin/env bash
git push origin main
git push origin_github main

git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
git push origin_github v0.1.0

python -m build
python -m twine upload dist/*
rm -rf dist
