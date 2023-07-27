# NYML

NYML (NedoYAML or Not a YAML) is yet another human-oriented data-serialization
language. It was inspired by shortcomings of YAML and sacrifices self-descriptiveness
in favor of less astonishment for humans.

TL;DR: in NYML you don't have to worry if your string looks like a number, list
or boolean, you just write it as-is.

In order for machine to be able to read NYML document properly an out-of-band
document format descriptions, called schemas, are used. Schemas are usually expressed
as NYML documents themselves. Unless a schema is applied, all simple fields in
the document are considered to be strings.

## Requirements

Python >= 3.7

## Installation

NYML is available on PyPI:

```console
$ python3 -m pip install nyml
```
