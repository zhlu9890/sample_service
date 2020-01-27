# SampleService


Build status (master):
[![Build Status](https://travis-ci.org/kbaseIncubator/sample_service.svg?branch=master)](https://travis-ci.org/kbaseIncubator/sample_service)
[![Coverage Status](https://coveralls.io/repos/github/kbaseIncubator/sample_service/badge.svg?branch=master)](https://coveralls.io/github/kbaseIncubator/sample_service?branch=master)

This is a [KBase](https://kbase.us) module generated by the [KBase Software Development Kit (SDK)](https://github.com/kbase/kb_sdk).

You will need to have the SDK installed to use this module. [Learn more about the SDK and how to use it](https://kbase.github.io/kb_sdk_docs/).

You can also learn more about the apps implemented in this module from its [catalog page](https://narrative.kbase.us/#catalog/modules/SampleService) or its [spec file](SampleService.spec).

# Description

The Sample Service stores information regarding experimental samples taken from the environment.
It supports Access Control Lists for each sample, subsample trees, and modular metadata
validation.

The SDK API specification for the service is contained in the `SampleService.spec` file. An indexed
interactive version is
[also available](http://htmlpreview.github.io/?https://github.com/kbaseIncubator/sample_service/blob/master/SampleService.html).

# Setup and test

The Sample Service requires ArangoDB 3.5.1+ with RocksDB as the storage engine.

To run tests, MongoDB 3.6+ and the KBase Jars file repo are also required.

See `.travis.yml` for an example of how to set up tests, including creating a `test.cfg` file
from the `test/test.cfg.example` file.

Once the dependencies are installed, run:

```
pipenv install --dev
pipenv shell
make test-sdkless
```

`kb-sdk test` does not currently pass. 


# Installation from another module

To use this code in another SDK module, call `kb-sdk install SampleService` in the other module's root directory.

# Help

You may find the answers to your questions in our [FAQ](https://kbase.github.io/kb_sdk_docs/references/questions_and_answers.html) or [Troubleshooting Guide](https://kbase.github.io/kb_sdk_docs/references/troubleshooting.html).

# Configuring the server

The server has several startup parameters beyond the standard SDK-provided parameters
that must be configured in the Catalog Service by a Catalog Service administrator in order
for the service to run. These are documented in the `deploy.cfg` file. 

# API Error codes

Error messages returned from the API may be general errors without a specific structure to
the error string or messages that have error codes embedded in the error string. The latter
*usually* indicate that the user/client has sent bad input, while the former indicate a server
error. A message with an error code has the following structure:

```
Sample service error code <error code> <error type>: <message>
```

There is a 1:1 mapping from error code to error type; error type is simply a more readable
version of the error code. The error type **may change** for an error code, but the error code
for a specfic error will not.

The current error codes are:
```
20000 Unauthorized
30000 Missing input parameter
30001 Illegal input parameter
30010 Metadata validation failed
40000 Concurrency violation
50000 No such user
50010 No such sample
50020 No such sample version
60000 Unsupported operation
```

# Metadata validation

Each node in the sample tree accepted by the `create_sample` method may contain controlled and
user metadata. User metadata is not validated other than very basic size checks, while controlled
metadata is validated based on configured validation rules.

## All metadata

For all metadata, map keys are are limited to 256 characters and values are limited to 1024
characters. Keys may not contain any control characters, while values may contain tabs and
new lines.

## Controlled metadata

Controlled metadata is subject to validation - no metadata is allowed that does not pass
validation or does not have a validator assigned.

Metadata validators are modular and can be added to the service via configuration without
changing the service core code. Multiple validators can be assigned to each metadata key.

Sample metadata has the following structure (also see the service spec file):

```
{"metadata_key_1: {"metadata_value_key_1_1": "metadata_value_1_1",
                                        ...
                   "metadata_value_key_1_N": "metadata_value_1_N",
                   },
                      ...
 "metadata_key_N: {"metadata_value_key_N_1": "metadata_value_N_1",
                                        ...
                   "metadata_value_key_N_N": "metadata_value_N_N",
                   }
}
```
Metadata values are primitives: a string, float, integer, or boolean.

A simple example:
```
{"temperature": {"measurement": 1.0,
                 "units": "Kelvin"
                 },
 "location": {"name": "Castle Geyser",
              "lat": 44.463816,
              "long": -110.836471
              }
}
```

In this case, a validator would need to be assigned to the `temperature` and `location`
metadata keys. Validators are `python` callables that accept the value of the key as the only
argument. E.g. in the case of the `temperature` key, the argument to the function would be:

```
{"measurement": 1.0,
 "units": "Kelvin"
 }
```

If the metadata is incorrect, the validator should return an error message as a string. Otherwise
it should return `None` unless the validator cannot validate the metadata due to some
uncontrollable error (e.g. it can't connect to an external server after a reasonable timeout),
in which case it should throw an exception.

 Validators are built by a builder function specified in the configuration (see below).
 The builder is passed any parameters specified in the configuration as a
 mapping. This allows the builder function to set up any necessary state for the validator
 before returning the validator for use. Examine the validators in
`SampleService.core.validators.builtin` for examples. A very simple example might be:

 ```python
 def enum_builder(params: Dict[str, str]
        ) -> Callable[[Dict[str, Union[float, int, bool, str]]], Optional[str]]:
    # should handle errors better here
    enums = {e.strip() for e in d['enums'].split(',')}
    key = d['key']

    def validate_enum(value: Dict[str, Union[float, int, bool, str]]) -> Optional[str]:
        if value.get(key) not in enums:
            return f'Illegal value for key {key}: {value.get(key)}'
        return None

    return validate_enum
```

### Configuration

The `deploy.cfg` configuration file contains a key, `metadata-validator-config-url`, that if
provided must be a url that points to a validator configuration file. The configuration file
is loaded on service startup and used to configure the metadata validators. If changes are made
to the configuration file the service must be restarted to reconfigure the validators.

The configuration file uses the YAML format and is validated against the following JSONSchema:

```
{
    'type': 'object',
    'additionalProperties': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'module': {'type': 'string'},
                'callable-builder': {'type': 'string'},
                'parameters': {'type': 'object'}
            },
            'additionalProperties': False,
            'required': ['module', 'callable-builder']
        }
    }
}
```

The configuration consists of a mapping of metadata keys to a list of validator specifications
per key. Each validator is run against the metadata value in order. The `module` key is a python
import path for the module containing a builder function for the validator, while the
`callable-builder` key is the name of the function within the module that can be called to 
create the validator. `parameters` contains a mapping that is passed directly to the callable
builder. The builder is expected to return a callable that accepts a mapping of
`str -> Union[str, int, float, bool]`.

A simple configuration might look like:
```
foo:
    - module: SampleService.core.validators.builtin
      callable-builder: noop
stringlen:
    - module: SampleService.core.validators.builtin
      callable-builder: string
      parameters:
        max-len: 5
    - module: SampleService.core.validators.builtin
      callable-builder: string
      parameters:
        keys: spcky
        max-len: 2
```

In this case any value for the `foo` key is allowed, as the `noop` validator is assigned to the
key. Note that if no validator was assigned to `foo`, including that key in the metadata would
cause a validation error.
The `stringlen` key has two validators assigned and any metadata under that key must pass
both validators. The first validator ensures that no keys or value strings in in the metadata map
are longer than 5 characters, and the second ensures that the value of the `spcky` key is a
string of no more than two characters. See the documentation for the `string` validator (below)
for more information.

### Built in validators

All built in validators are in the `SampleService.core.validators.builtin` module.

#### noop

Example configuration:
```
metadatakey:
    - module: SampleService.core.validators.builtin
      callable-builder: noop
```

This validator accepts any and all values.

#### string

Example configuration:
```
metadatakey:
    - module: SampleService.core.validators.builtin
      callable-builder: string
      parameters:
        keys: ['key1', 'key2']
        required: True
        max-len: 10
```

* `keys` is either a string or a list of strings and determines which keys will be checked by the
  validator. If the key exists, its value must be a string or `None` (`null` in JSON-speak).
* `required` requires any keys in the `keys` field to exist in the map, although their value may
  still be `None`.
* `max-len` determines the maximum length in characters of the values of the keys listed in `keys`.
  If `keys` is not supplied, then it determines the maximum length of all keys and string values
  in the metadata value map.

#### enum

Example configuration:
```
metadatakey:
    - module: SampleService.core.validators.builtin
      callable-builder: enum
      parameters:
        keys: ['key1', 'key2']
        allowed-values: ['red', 'blue', 'green]
```

* `allowed-values` is a list of primitives - strings, integers, floats, or booleans - that are
  allowed metadata values. If `keys` is not supplied, all values in the metadata value mapping must
  be one of the allowed values.
* `keys` is either a string or a list of strings and determines which keys will be checked by the
  validator. The key must exist and its value must be one of the `allowed-values`.