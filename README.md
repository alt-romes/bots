I wrote this a long time ago when I was working on it. (I don't recommend using this)
---
(check "how to write a good readme.md")

Preparation:

| Rename `configsample.py` to `config.py`. Fill in with username and passwords.

| Create a directory called "logs", the program can't create directories.

| Install chromedriver to path

| `pip install selenium`


Running:

```bash
python bothub.py

to use curses interface: (might be buggy, stopped using it very early on)
python bothub.py --curses  

crontab
export PATH=$PATH:chromedriverpath; cd into directory; full/path/to/python bothub.py
```
