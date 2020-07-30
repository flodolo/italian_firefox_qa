# Italian QA scripts for Firefox and Fennec

To run the script, use `scripts/check_strings.sh` (it will create and activate a virtualenv with Python 3 and install dependencies).


## Hunspell

If you’re using macOS, you need to install Hunspell via `brew`

```
brew install hunspell
```

Be aware of the multiple issues existing ([one](https://github.com/blatinier/pyhunspell/issues/26), [two](https://github.com/blatinier/pyhunspell/issues/33)).

In my case, this worked after manually activating the virtualenv

```
ln -s /usr/local/lib/libhunspell-1.7.a /usr/local/lib/libhunspell.a
ln -s /usr/local/Cellar/hunspell/1.7.0_2/lib/libhunspell-1.7.dylib /usr/local/Cellar/hunspell/1.7.0_2/lib/libhunspell.dylib
CFLAGS=$(pkg-config --cflags hunspell) LDFLAGS=$(pkg-config --libs hunspell) pip3 install hunspell
```
