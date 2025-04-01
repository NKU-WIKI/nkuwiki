@echo off
chcp 936 >nul
git stash
git pull --rebase
git stash pop
git add .
git commit -m "update webpage"
git push
pause