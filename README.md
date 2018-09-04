# Italian QA scripts for Firefox and Fennec

This script requires `python3`. To run the script, use `scripts/check_strings.sh` (it will create and activate a virtualenv).


## Hunspell
If you’re using macOS, you need to install Hunspell via brew

```
brew install hunspell
```

Be aware of the multiple issues existing ([one](https://github.com/blatinier/pyhunspell/issues/26), [two](https://github.com/blatinier/pyhunspell/issues/33)).

In my case, this worked after manually activating the virtualenv

```
brew install hunspell
ln -s /usr/local/lib/libhunspell-1.6.a /usr/local/lib/libhunspell.a
ln -s /usr/local/Cellar/hunspell/1.6.2/lib/libhunspell-1.6.0.dylib /usr/local/Cellar/hunspell/1.6.2/lib/libhunspell.dylib
CFLAGS=$(pkg-config --cflags hunspell) LDFLAGS=$(pkg-config --libs hunspell) pip3 install hunspell
```

## NLTK

Manually activate the virtualenv, open `python` and run

```
import nltk
nltk.download('punkt')
```
